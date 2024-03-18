from dataclasses import dataclass
import math

@dataclass
class Home:
    latitude: float
    longitude: float
    home_year: int
    home_type: str
    home_outer_construction_type: str
    heating_setpoint_c: int
    cooling_setpoint_c: int
    conditioned_floor_area_sq_m: int
    number_of_stories: int
    ceiling_height_m: int
    wall_r_value_defined: bool
    wall_insulation_r_value_imperial_user: float
    ach50_defined: bool
    ach50_user: int
    south_facing_window_size_sq_m: int
    window_year: int
    window_r_value_defined: bool
    window_r_value_imperial_user: int
    window_shgc_defined: bool
    window_solar_heat_gain_coefficient_user: int

    @property
    def wall_insulation_r_value_construction(self) -> float:
        construction_types = ["Brick", "Lumber", "Stone", "Vinyl", "Fiber Cement", "Stucco", "Composite"]
        # Sources:
        # All: https://www.ahfc.us/iceimages/manuals/building_manual_ap_1.pdf
        # Brick: https://insulationessentials.com.au/building-materials-for-walls/
        # Brick: https://forum.heatinghelp.com/discussion/96219/older-home-r-value-estimates
        # Lumber: https://www.ahfc.us/iceimages/manuals/building_manual_ap_1.pdf
        # Stone: https://www.diychatroom.com/threads/r-value-of-solid-stone-wall.54919/
        # Vinyl: https://www.brickface.com/understanding-the-r-value-of-siding/#:~:text=Good%20quality%20insulated%20vinyl%20siding,than%20many%20other%20building%20materials.
        # Fiber cement: https://www.progressivefoam.com/problems-fiber-cement-siding/#:~:text=According%20to%20Table%205%2D1,at%20R%2D2.0%20%2D%203.5.
        # Stucco: https://www.dnr.louisiana.gov/assets/TAD/education/ECEP/constr/b/b.htm
        # Composite: https://www.e-education.psu.edu/egee102/node/2064
        # These are very rough and depend a lot on thickness of the material used and other elements of the wall.
        # Later homes will probably also be insulated.
        construction_R = [3.5, 4.38, 0.43, 0.61, 0.15, 0.2, 2]
        for i in range(len(construction_types)):
            if self.home_outer_construction_type == construction_types[i]:
                return construction_R[i]
    @property
    def wall_insulation_r_value_imperial(self) -> float:
        if self.wall_r_value_defined == True:
            return self.wall_insulation_r_value_imperial_user
        else:
            # Source: https://energysmartohio.com/uncategorized/do-the-walls-of-my-old-house-need-to-be-insulated/
            if self.home_year <= 1965:
                # Basic assumption - I assume the wall's R value is at least 2
                if self.wall_insulation_r_value_construction < 2:
                    return 2
                else:
                    return self.wall_insulation_r_value_construction
            elif self.home_year <= 1970:
                return self.wall_insulation_r_value_construction + 8
            elif self.home_year <= 1990:
                return self.wall_insulation_r_value_construction + 11
            else:
                return self.wall_insulation_r_value_construction + 13

    @property
    def ach50(self) -> int:
        if self.ach50_defined == True:
            return self.ach50_user
        else:
            # Calculated using a paper that uses "normalized leakage"
            # Source: https://www.osti.gov/servlets/purl/816784
            # There's a beta_3 for a binary variable for "leaks" but beta_3 does not appear to be disclosed.
            # These values are from page 28 for conventional homes.
            beta_0 = 2.07 * 10**1
            beta_1 = -1.07 * 10**-2
            beta_2 = -2.20 * 10**-3

            NL_value = math.exp(beta_0 + beta_1 * self.home_year + beta_2 * self.conditioned_floor_area_sq_m)

            # The paper also discusses conversions to ACH50 using just NL and the height.

            ach50_calc = 48 * (2.5 / self.ceiling_height_m) ** 0.3 * NL_value / self.ceiling_height_m
            return ach50_calc

    @property
    def window_r_value_imperial(self) -> float:

        if self.window_r_value_defined == True:
            return self.window_r_value_imperial_user
        else:
            # Somewhat arbitrary, double-pane windows became standard in the 70s
            # Source: https://www.thespruce.com/double-glazed-windows-1821739

            # Triple pane windows are still relatively rare
            # Source: https://www.pnnl.gov/news-media/how-triple-pane-windows-stop-energy-and-money-flying-out-window

            # low e windows broke through around 2005
            # Source: https://bipartisanpolicy.org/download/?file=/wp-content/uploads/2013/03/Case-Low-e-Windows.pdf
            if self.window_year <= 1975:
                return 1
            elif self.window_year <= 2005:
                return 2
            else:
                return 2.5

    @property
    def window_solar_heat_gain_coefficient(self) -> float:

        if self.window_shgc_defined == True:
            return self.window_solar_heat_gain_coefficient_user
        else:
            # Single vs. double pane
            # source: https://esource.bizenergyadvisor.com/article/windows
            if self.window_year <= 1975:
                return 0.72
            elif self.window_year <= 2005:
                return 0.60
            else:
                return 0.34

    @property
    def building_volume_cu_m(self) -> int:
        return self.conditioned_floor_area_sq_m * self.ceiling_height_m * self.number_of_stories

    @property
    def building_perimeter_m(self) -> float:
        # Assume the building is a 1-story square
        return math.sqrt(self.conditioned_floor_area_sq_m) * 4

    @property
    def surface_area_to_area_sq_m(self) -> float:
        # Surface area exposed to air = wall area + roof area (~= floor area, for 1-story building)
        return self.building_perimeter_m * self.ceiling_height_m + self.conditioned_floor_area_sq_m

    @property
    def ach_natural(self) -> float:
        # "Natural" air changes per hour can be roughly estimated from ACH50 with an "LBL_FACTOR"
        # https://building-performance.org/bpa-journal/ach50-achnat/
        LBL_FACTOR = 17
        return self.ach50 / LBL_FACTOR

    @property
    def wall_insulation_r_value_si(self) -> float:
        return self.wall_insulation_r_value_imperial / 5.67  # SI units: m^2 °K/W

    @property
    def window_insulation_r_value_si(self) -> float:
        return self.window_r_value_imperial / 5.67  # SI units: m^2 °K/W

    @property
    def building_heat_capacity(self) -> int:
        # Building heat capacity
        # How much energy (in kJ) do you have to put into the building to change the indoor temperature by 1 degree?
        # Heat capacity unit: Joules per Kelvin degree (kJ/K)
        # A proper treatment of these factors would include multiple thermal mass components,
        # because the walls, air, furniture, foundation, etc. all store heat differently.
        # More info: https://www.greenspec.co.uk/building-design/thermal-mass/
        HEAT_CAPACITY_FUDGE_FACTOR = 1e5
        return self.building_volume_cu_m * HEAT_CAPACITY_FUDGE_FACTOR
