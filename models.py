from dataclasses import dataclass, asdict, field, fields
from typing import Optional
from deta import Deta
import streamlit as st
import numpy as np
import operator

deta = Deta(st.secrets['deta_key'])
pws = deta.Base('pws')
contaminants = deta.Base('contaminants_db')
readings = deta.Base('readings')

@dataclass
class WaterUtility:
    name: str
    pwsid: str
    street: str
    city_state_zip: str
    supply: str
    treatment: str
    territory: list[str]
    last_updated: int
    pdf: str
    publish: str


    def __repr__(self):
        return self.pwsid

    # Get all "city state, zip" for all water utilities
    def get_all() -> list[str]:
        territory = ['']
        wutility = pws.fetch().items
        for each in wutility:
            territory += each['territory']
        return territory
    
    def get_all_pwsid() -> list[str]:
        pwsid_lst = ['']
        pwsid = pws.fetch().items
        for each in pwsid:
            pwsid_lst.append(each['pwsid'])
        return pwsid_lst

    def add_to_db(self):
        pws.insert(asdict(self))

    # Create a function to sort contaminants in descending order of contaminant reading relative to standard
    def get_primary(readings: list):
        '''Rankings only with "Primary" contaminants'''
        primary_lst = Primary.create_primary_list(readings)
        return primary_lst
    
    def get_secondary(readings: list):
        secondary_dict = Secondary.create_secondary_dict(readings)
        return secondary_dict


    # Create a staticmethod to return WaterUtility object by territory
    @staticmethod
    @st.experimental_memo(show_spinner=False)
    def get_from_db(territory: str):
        # Fetch item by key
        utility = pws.fetch({'territory?contains': territory}).items[0]
        utility.pop('key')
        return WaterUtility(**utility)

@dataclass
class Contaminant:
    name: str
    alt_names: list[str]
    standard: str
    type: str
    units: str
    AC: Optional[bool] = False
    RO: Optional[bool] = False
    Ion: Optional[bool] = False
    mclg: Optional[float] = np.nan
    mcl: Optional[float] = np.nan
    risk: Optional[str] = None
    source: Optional[str] = None
    rul: Optional[str] = None
    effects: Optional[str] = None

    def __repr__(self):
        return self.name

    # Returns a short summary of what filtration method is recommended
    def get_filter_rec(self):
        rec_list = []
        if self.RO: 
            rec_list.append('Reverse Osmosis filtration')
        else:
            rec_list.append('~~Reverse Osmosis filtration~~')

        if self.AC: 
            rec_list.append('Activated Carbon filtration')
        else:
            rec_list.append('~~Activated Carbon filtering~~')

        if self.Ion: 
            rec_list.append('Ion Exchange')
        else: 
            rec_list.append('~~Ion Exchange~~')

        return rec_list


    # Get all contaminant names
    def get_all() -> list[str]:
        cont_lst = ['']
        cont = contaminants.fetch().items
        for each in cont:
            cont_lst.append(each['name'])
        return cont_lst
    
    # Get all units
    def get_all_units() -> list[str]:
        units_lst = ['']
        units = contaminants.fetch().items
        for each in units:
            units_lst.append(each['units'])
        return units_lst
    
    def add_to_db(self):
        contaminants.insert(asdict(self))

    def get_units_name(self):
        full_name = ''
        if self.units == 'ppt': full_name = 'parts per trillion'
        elif self.units == 'ppb': full_name = 'parts per billion'
        elif self.units == 'ppm': full_name = 'parts per million'
        return f'{full_name} ({self.units})'

    # Create a staticmethod to return Contaminant object by name
    @staticmethod
    @st.experimental_memo(show_spinner=False)
    def get_from_db(ctmnt: str):
        # Fetch item by key
        contaminant = contaminants.fetch([{'name': ctmnt}, {'alt_names?contains': ctmnt}])
        if contaminant.count > 0:
            contaminant.items[0].pop('key')
            return Contaminant(**contaminant.items[0])
        else:
            return None



@dataclass
class ContaminantReading:
    year: int
    origin: str
    contaminant: Contaminant
    units: str
    max: Optional[float] = np.nan
    min: Optional[float] = np.nan
    annual_avg: Optional[float] = np.nan
    lraa: Optional[float] = np.nan
    raa: Optional[float] = np.nan
    ninetieth_perc: Optional[float] = np.nan
    violation: Optional[int] = np.nan
    sample_num: Optional[int] = np.nan

    # Create a staticmethod to return ContaminantReading object by WaterUtility

    def add_to_db(self):
        cr = asdict(self)
        readings.insert(cr)
    
    
    # Get a list of ContaminantReading dicts from database
    @staticmethod
    @st.experimental_memo(show_spinner=False)
    def get_from_db(wutility: WaterUtility) -> list[dict]:
        cr_list = []
        creadings = readings.fetch({'origin': wutility.pwsid, 'year': wutility.last_updated-1}).items
        completion = st.progress(0.0)
        count = 1
        for cr in creadings:
            completion.progress(count/len(creadings))
            count +=1
            cr.pop('key')
            cr_obj = ContaminantReading(**cr)
            cont_obj = Contaminant.get_from_db(cr_obj.contaminant)
            cr_obj.contaminant = cont_obj
            if cr_obj.contaminant == None: continue
            cr_list.append(cr_obj)
        return cr_list

@dataclass
class Secondary:
    year: int
    contaminant: Contaminant
    rul: str
    max: float

    @staticmethod
    def create_secondary_dict(readings):
        secondary = {}
        for each in readings:
            if each.contaminant.standard == 'Secondary':
                obj = Secondary(
                    year=each.year,
                    contaminant=each.contaminant,
                    rul=each.contaminant.rul,
                    max=each.max
                )
                secondary[each.contaminant.name] = obj
        return secondary


@dataclass
class Primary:
    year: int
    contaminant: Contaminant
    mclg: float
    mcl: float
    max_reading: float = np.nan
    perc: float = np.nan
    factor: float = field(init=False)


    def __post_init__(self):
        if float(self.mclg) == 0:
            self.factor = float('inf')
        elif self.max_reading == '':
            self.factor = float(self.perc)/float(self.mclg) - 1
        else:
            self.factor = float(self.max_reading)/float(self.mclg) - 1

    
    @staticmethod
    def create_primary_list(readings):
        primary = []
        for each in readings:
            if each.contaminant.standard == 'Primary':
                each = calibrate_units(each)
                obj = Primary(
                    year=each.year,
                    contaminant=each.contaminant,
                    max_reading=each.max,
                    mclg=each.contaminant.mclg,
                    mcl=each.contaminant.mcl,
                    perc=each.ninetieth_perc
                )
                primary.append(obj)
        return sorted(primary, key=operator.attrgetter('factor'), reverse=True)



def calibrate_units(c_reading):
    if c_reading.contaminant.units == c_reading.units:
        return c_reading
    
    if c_reading.contaminant.units == 'ppt':
        if c_reading.units == 'ppb': c_reading.max = float(c_reading.max) * 1000
        if c_reading.units == 'ppm': c_reading.max = float(c_reading.max) * 1000000
    
    elif c_reading.contaminant.units == 'ppb':
        if c_reading.units == 'ppt': c_reading.max = float(c_reading.max) / 1000
        if c_reading.units == 'ppm': c_reading.max = float(c_reading.max) * 1000

    elif c_reading.contaminant.units == 'ppm':
        if c_reading.units == 'ppt': c_reading.max = float(c_reading.max) / 1000000
        if c_reading.units == 'ppb': c_reading.max = float(c_reading.max) / 1000

    return c_reading

