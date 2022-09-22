#include "udf.h"
#include "math.h"
#include "stdio.h"

#define kay 0.41       /*constants*/
#define cmu 0.09
#define yo 0.003
#define PI 3.14159265

//Global variables, which shouldn't be reset each time the below functions are called
real ustar = 0;
real v_naught;
real direction = 0;
float data[145][4]{};
real ustar_k = 0;
real ustar_e = 0;
real ustar_x = 0;
real ustar_z = 0;
real radiation = 0;
real s_rad = 0;
real soilheatflux = 0;
real soil_temp;

DEFINE_ADJUST(weather_data_read_v1_0_5_3_8,d)
{
/*Reads in the weather data (wind speed, direction, and radiation) from file fp,
assuming the wind speed is the speed at 10m above the ground
Sets ustar, which is used to determine the velocity profile, dissipation rate,
and turbulent kinetic energy
*/

    //Adjusts ustar, direction, radiation, and soil temp every 600s flow time
    int curr_ts;
    curr_ts = CURRENT_TIME;
    if (curr_ts % 600 == 0){


        int file_time;
        float speed, file_direction, temp, file_rad;
        FILE *fp;
        fp = fopen("C:/weather_data_h2_3_19.csv", "r");

        //Checks to make sure the file exists
        if (fp != NULL){

            //Takes csv file with 3 columns, column 1 = flow time/600, columm 2 = wind speed, column 3 = direction in degrees, column 4 = solar radiation data, column 5 = soil temp
            while(fscanf(fp, "%d %*[,] %f %*[,] %f %*[,] %f %*[,] %f %*[\n]", &file_time, &speed, &file_direction, &file_rad, &temp)!=EOF){
                //saves speed and direction to data array, where array index is equal to file time
                data[file_time][0] = speed;
                data[file_time][1] = file_direction;
                data[file_time][2] = file_rad;
                data[file_time][3] = temp;
            }
        }
        fclose(fp);

        //Sets current v_naught to wind speed at the current time in the file fp
        v_naught = data[int(floor(curr_ts/600))][0];

        //Corrects for limit of sensor and issue with no convection
        if (v_naught < 0.1){
            v_naught = 0.1;
        }

        //Sets direction based on orientation of mesh by converting degrees to align with vents instead of North and East
        direction = data[int(floor(curr_ts/600))][1];

        if (direction >= 259.6){
            direction -= 259.6;
        } else {
            direction += 100.4;
        }

        //Sets radiation to be used in DEFINE_SOLAR_INTENSITY (because a simple profile won't work...)
        radiation = data[int(floor(curr_ts/600))][2];

        //sets current soil temp for use in soilheatflux
        soil_temp = data[int(floor(curr_ts/600))][3];

        //Sets ustar, which is used for velocity profile, dissipation rate, and turbulent kinetic energy
        ustar = (v_naught*kay) / log((10 + yo) / yo);
    }
}


DEFINE_PROFILE(dissipation_rate_v1, t, i)
{
/*Sets dissipation rate at velocity inlet*/

    //Initialize variables
	real x[ND_ND]; //holds position vector
	real y;
	face_t f;

    //only runs this loop if ustar has changed since last check
    if (ustar != ustar_e){

        ustar_e = ustar;

        begin_f_loop(f, t)
        {
            F_CENTROID(x, f, t); //finds center of each face on inlet
            y = x[1]; //sets height equal to y
            F_PROFILE(f, t, i) = pow(ustar, 3) / (kay*(y + yo)); //outputs dissipation rate
        }
        end_f_loop(f, t)
    }
}


DEFINE_PROFILE(turbulent_kinetic_energy_v1, t, i)
{
/*Sets dissipation rate at velocity inlet*/

    //Initialize variables
	face_t f;

	//only runs this loop if ustar has changed since last check
	if (ustar != ustar_k){

        ustar_k = ustar;

        begin_f_loop(f, t)
        {
            F_PROFILE(f, t, i) = pow(ustar, 2) / sqrt(cmu); //outputs turbulent kinetic energy
        }
        end_f_loop(f, t)
	}
}


DEFINE_PROFILE(x_velocity_profile_v1, t, i)
 {
/*Sets x-component of velocity profile at velocity inlet*/

    //Initialize variables
    real x[ND_ND];    //holds the position vector
    real y;
    face_t f;
    real theta_x = cosf(direction*PI/180);

    //only runs this loop if ustar has changed since last check
    if (ustar != ustar_x){

        ustar_x = ustar;

        begin_f_loop(f,t)
          {
           F_CENTROID(x,f,t); //finds center of each face on inlet
           y = x[1]; //sets height equal to y
           F_PROFILE(f,t,i) = (ustar/kay)*log((y+yo)/yo) * theta_x; //outputs velocity
          }
        end_f_loop(f,t)
    }
 }


 DEFINE_PROFILE(z_velocity_profile_v1, t, i)
 {
/*Sets z-component of velocity profile at velocity inlet*/

    //Initialize variables
    real x[ND_ND];    //holds the position vector
    real y;
    face_t f;
    real theta_z = sinf(direction*PI/180);

    //only runs this loop if ustar has changed since last check
    if (ustar != ustar_z){

        ustar_z = ustar;

        begin_f_loop(f,t)
          {
           F_CENTROID(x,f,t); //finds center of each face on inlet
           y = x[1]; //sets height equal to y
           F_PROFILE(f,t,i) = (ustar/kay)*log((y+yo)/yo) * theta_z; //outputs velocity
          }
        end_f_loop(f,t)
    }
 }

DEFINE_GRAY_BAND_ABS_COEFF(user_gray_band_abs,c,t,nb)
{
    real abs_coeff = 0;
    real mass_fraction = C_YI(c, t, 0); //h2o mass fraction

    switch (nb)
    {
      case 0 : abs_coeff = 0; break;
      case 1 : abs_coeff = 6.9 * mass_fraction; break;
    }

    return abs_coeff;

}

DEFINE_EXECUTE_AT_END(set_humidity_rp_value_v1_1)
{
    real temp, e, pressure, dry_air_mass, max_water_mass, max_fraction, mass_fraction;
    real counter = 0;
    real humidity = 0;

    Thread *t;
    Domain *d;
    cell_t c;
    d = Get_Domain(1);
    int cell_ID[4] = {1078, 1099, 1111, 1096}; /* cell zones in high tunnel */
    for (int i = 0; i < 4; i++) //loops through each cell zone
    {
        t = Lookup_Thread(d, cell_ID[i]); //looks up thread for the cell zone that's currently being worked on
        begin_c_loop(c, t)
        {
            /* determine RH% */
            temp = C_T(c,t) - 273.15; //cell temp initial, C
            // find saturation pressure and convert to H2O mass fraction
            e = 611*exp((17.27*temp)/(237.3+temp)); //saturation vapor pressure, Pa
            pressure = C_P(c,t) + 101325; //adding 1atm to gauge pressure
            dry_air_mass = (29 * (pressure - e)*C_VOLUME(c,t))/(8.314*temp); //g/mol * J/m3 * m3 * K*mol/J * 1/K , final unit is g
            max_water_mass = (18 * e *C_VOLUME(c,t))/(8.314*temp); //maximum amount of water that can be held in the air at current temp
            max_fraction = max_water_mass/(max_water_mass + dry_air_mass); //mass fraction with max amount of water held in air
            //find species mass fraction, water-vapor is first species listed
            mass_fraction = C_YI(c, t, 0);

            humidity += (mass_fraction/max_fraction) * 100;
            counter+=1;
        }
        end_c_loop(c,t)
    }
    humidity /= counter;

    node_to_host_real_1(humidity);
    RP_Set_Real("humidity", humidity);
    humidity = RP_Get_Real("humidity");
    Message0("Humidity: %f\n", humidity);

}

DEFINE_REPORT_DEFINITION_FN(vents_open)
{
    int open;
    /* 0 - closed, 1 - open */
    open = RP_Get_Integer("vent");
    return open;
}

DEFINE_PROFILE(soil_heat_flux_v1_3, t, i)
{
// conductive heat flux soil, assume there is no radiative heat transfer because it gets blocked by canopy
// qh - heat (w), lambda - thermal conductivity (w/m*K), A - area (m2),
// d - thickness (m), deltaT - temperature difference between soil and air (K)
// heat flux = qh/A = (lambda * deltaT) / d

//initialize variables
    real lambda = 1;
    real d = 1;
    real deltaT;
    real area;
    face_t f;
    cell_t c0;
    Thread *t0;
    real counter = 0;
    real soilheatflux = 0;

//find deltaT at each mesh face on the floor
    begin_f_loop(f,t)
    {
        //compare soil temp from Penn State with air temperature of adjacent cell
        c0 = F_C0(f,t);
        t0 = F_C0_THREAD(f,t);
        //if deltaT is positive, heat goes into floor; if deltaT is negative, heat goes into tunnel
        deltaT = C_T(c0,t0) - soil_temp;
        //set heat flux here
        F_PROFILE(f,t,i) = (lambda * deltaT) / d; //w/m^2
        soilheatflux += (lambda * deltaT) / d; //accumulates all soil heat flux calculations to average at end
        counter +=1;
    }
    end_f_loop(f,t)
    soilheatflux /= counter; //average soil heat flux, w/m^2
}

DEFINE_EXECUTE_AT_END(condensation_v1_2_2_60s_15cm_open)
{
// condensation on surfaces and plants, assume liquid water is removed from the system when this happens
    int curr_ts;
    curr_ts = CURRENT_TIME;

    // this runs at the end of every 60s
    if (curr_ts % 60 == 0 ){
            //change 1st modulus for timestep size change

        // initialize variables
        Domain *d;
        d = Get_Domain(1);
        cell_t c;
        cell_t c0;
        face_t f;
        Thread *t;
        Thread *t0;
        int cell_ID [3] = {1099, 1111, 1096}; // Zone ID for fluid_medium_plant_1,2,3
        int face_ID [7] = {3, 412, 6, 7, 9, 10, 4662}; // Zone ID for high tunnel shadow walls (except roof vent, which is roof-vent-in) (not including 0 to 15 side vents) and floor-high-tunnel --> all area vectors point out
        real temp_i;
        real e;
        real pressure;
        real dry_air_mass;
        real max_water_mass;
        real max_fraction;
        real mass_fraction_i;
        real water_mass_i;
        real remove_mass;
        real latent;
        real Q;
        real temp_f;
        float c_crop = 3.2537; //kJ/kg*C
        float d_crop = 0.9*1000 + 0.1*1500; //kg/m^3
        float c_plastic = 1.900; //kJ/kg*C
        float d_plastic = 920; //kg/m^3
        int file_write;

        // loop over appropriate faces and cells --> faces = inside of high tunnel plastic, high tunnel floor; cells = plants
        for (int i = 0; i < 3; i++) //loops through each cell zone
            {
                file_write = 0; // restart file_write to allow writing
                t = Lookup_Thread(d, cell_ID[i]); //looks up thread for the cell zone that's currently being worked on
                Message0("Zone ID = %d Thread = %d\n", cell_ID[i], t);
                begin_c_loop(c, t)
                {
                // check if air is oversaturated with water vapor, i.e. RH > 100%
                    temp_i = C_T(c,t) - 273.15; //cell temp initial, C
                    // find saturation pressure and convert to H2O mass fraction
                    e = 611*exp((17.27*temp_i)/(237.3+temp_i)); //saturation vapor pressure, Pa
                    pressure = C_P(c,t) + 101325; //adding 1atm to gauge pressure
                    dry_air_mass = (29 * (pressure - e)*C_VOLUME(c,t))/(8.314*temp_i); //g/mol * J/m3 * m3 * K*mol/J * 1/K , final unit is g
                    max_water_mass = (18 * e *C_VOLUME(c,t))/(8.314*temp_i); //maximum amount of water that can be held in the air at current temp
                    max_fraction = max_water_mass/(max_water_mass + dry_air_mass); //mass fraction with max amount of water held in air
                    //find species mass fraction, water-vapor is first species listed
                    mass_fraction_i = C_YI(c, t, 0);


                // condense on surface, if oversaturated, by removing water vapor from air and heating the surface
                    if (mass_fraction_i > max_fraction){
                        // water to be removed
                        water_mass_i = (mass_fraction_i * dry_air_mass)/(1 - mass_fraction_i);
                        remove_mass = water_mass_i - max_water_mass; // g
                        // set H2O mass fraction to max
                        C_YI(c, t, 0) = max_fraction;

                        //calculate latent heat to be removed
                        latent = 2500.8 - 2.36*temp_i + 0.0016*pow(temp_i,2) - 0.00006*pow(temp_i,3); //kJ/kg
                        Q = (remove_mass/1000)*latent; //(g * 1kg/1000g *kJ/kg) = kJ

                        //calculate and write final temp
                        temp_f = C_T(c,t) + Q/(c_crop*d_crop*C_VOLUME(c,t)); //kJ / kJ/kg*C * kg/m^3 * m^3 = C; +Q because heat is added
                        C_T(c,t) = temp_f;

                        // write to file the time step and location of condensation
                        if (file_write == 0){
                            FILE *fp;
                            fp = fopen("C:/Users/Rutgers/Desktop/David_Lewus_Research/CFD/Energy_Model_v3/condensation.txt", "a");
                            fprintf(fp, "%d %d\n", curr_ts, cell_ID[i]);
                            fclose(fp);
                            file_write = 1;
                        }

                    }
                }
                end_c_loop(c, t)
            }
        // for faces, look at adjacent cell to decide is condensation occurs there --> assume condensation happens at face surface based off activities in the cell
        for (int i = 0; i < 3; i++) //loops through each face zone
            {
                file_write = 0; // restart file_write to allow writing
                t = Lookup_Thread(d, face_ID[i]); //looks up thread for the face zone that's currently being worked on
                Message0("Zone ID = %d Thread = %d\n", face_ID[i], t);
                begin_f_loop(f, t)
                {
                // check if air is oversaturated with water vapor, i.e. RH > 100%
                    // look at neighboring cell, inside the tunnel
                    c0 = F_C0(f,t);
                    t0 = F_C0_THREAD(f,t);

                    // find saturation pressure and convert to H2O mass fraction
                    temp_i = C_T(c0,t0) - 273.15; //cell temp initial, C
                    e = 611*exp((17.27*temp_i)/(237.3+temp_i)); //saturation vapor pressure, Pa
                    pressure = C_P(c0,t0) + 101325; //adding 1atm to gauge pressure
                    dry_air_mass = (29 * (pressure - e)*C_VOLUME(c0,t0))/(8.314*temp_i); //g/mol * J/m3 * m3 * K*mol/J * 1/K , final unit is g
                    max_water_mass = (18 * e * C_VOLUME(c0,t0))/(8.314*temp_i); //maximum amount of water that can be held in the air at current temp
                    max_fraction = max_water_mass/(max_water_mass + dry_air_mass); //mass fraction with max amount of water held in air
                    //find species mass fraction, water-vapor is first species listed
                    mass_fraction_i = C_YI(c0, t0, 0);


                // condense on surface, if oversaturated, by removing water vapor from air and heating the surface
                    if (mass_fraction_i > max_fraction){
                        // water to be removed
                        water_mass_i = (mass_fraction_i * dry_air_mass)/(1 - mass_fraction_i);
                        remove_mass = water_mass_i - max_water_mass; // g
                        // set H2O mass fraction to max
                        C_YI(c0, t0, 0) = max_fraction;

                        //calculate latent heat to be removed
                        latent = 2500.8 - 2.36*temp_i + 0.0016*pow(temp_i,2) - 0.00006*pow(temp_i,3); //kJ/kg
                        Q = (remove_mass/1000)*latent; //(g * 1kg/1000g *kJ/kg) = kJ

                        //calculate and write final temp
                        temp_f = C_T(c0,t0) + Q/(c_plastic*d_plastic*C_VOLUME(c0,t0)); //kJ / kJ/kg*C * kg/m^3 * m^3 = C; +Q because heat is added
                        C_T(c0,t0) = temp_f;

                        // write to file the time step and location of condensation
                        if (file_write == 0){
                            FILE *fp;
                            fp = fopen("C:/Users/Rutgers/Desktop/David_Lewus_Research/CFD/Energy_Model_v3/condensation.txt", "a");
                            fprintf(fp, "%d %d\n", curr_ts, face_ID[i]);
                            fclose(fp);
                            file_write = 1;
                        }
                    }
                }
                end_f_loop(f, t)
            }
        }
}

DEFINE_EXECUTE_AT_END(condensation_v1_2_2_60s_15cm_closed)
{
// condensation on surfaces and plants, assume liquid water is removed from the system when this happens
    int curr_ts;
    curr_ts = CURRENT_TIME;

    // this runs at the end of every 60s
    if (curr_ts % 60 == 0 ){
            //change 1st modulus for timestep size change

        // initialize variables
        Domain *d;
        d = Get_Domain(1);
        cell_t c;
        cell_t c0;
        face_t f;
        Thread *t;
        Thread *t0;
        int cell_ID [3] = {1099, 1111, 1096}; // Zone ID for fluid_medium_plant_1,2,3
        int face_ID [9] = {3, 412, 5, 6, 7, 8, 9, 10, 4662}; // Zone ID for high tunnel shadow walls (except roof vent, which is roof-vent-in) and floor-high-tunnel --> all area vectors point out
        real temp_i;
        real e;
        real pressure;
        real dry_air_mass;
        real max_water_mass;
        real max_fraction;
        real mass_fraction_i;
        real water_mass_i;
        real remove_mass;
        real latent;
        real Q;
        real temp_f;
        float c_crop = 3.2537; //kJ/kg*C
        float d_crop = 0.9*1000 + 0.1*1500; //kg/m^3
        float c_plastic = 1.900; //kJ/kg*C
        float d_plastic = 920; //kg/m^3
        int file_write;

        // loop over appropriate faces and cells --> faces = inside of high tunnel plastic, high tunnel floor; cells = plants
        for (int i = 0; i < 3; i++) //loops through each cell zone
            {
                file_write = 0; // restart file_write to allow writing
                t = Lookup_Thread(d, cell_ID[i]); //looks up thread for the cell zone that's currently being worked on
                Message0("Zone ID = %d Thread = %d\n", cell_ID[i], t);
                begin_c_loop(c, t)
                {
                // check if air is oversaturated with water vapor, i.e. RH > 100%
                    temp_i = C_T(c,t) - 273.15; //cell temp initial, C
                    // find saturation pressure and convert to H2O mass fraction
                    e = 611*exp((17.27*temp_i)/(237.3+temp_i)); //saturation vapor pressure, Pa
                    pressure = C_P(c,t) + 101325; //adding 1atm to gauge pressure
                    dry_air_mass = (29 * (pressure - e)*C_VOLUME(c,t))/(8.314*temp_i); //g/mol * J/m3 * m3 * K*mol/J * 1/K , final unit is g
                    max_water_mass = (18 * e *C_VOLUME(c,t))/(8.314*temp_i); //maximum amount of water that can be held in the air at current temp
                    max_fraction = max_water_mass/(max_water_mass + dry_air_mass); //mass fraction with max amount of water held in air
                    //find species mass fraction, water-vapor is first species listed
                    mass_fraction_i = C_YI(c, t, 0);


                // condense on surface, if oversaturated, by removing water vapor from air and heating the surface
                    if (mass_fraction_i > max_fraction){
                        // water to be removed
                        water_mass_i = (mass_fraction_i * dry_air_mass)/(1 - mass_fraction_i);
                        remove_mass = water_mass_i - max_water_mass; // g
                        // set H2O mass fraction to max
                        C_YI(c, t, 0) = max_fraction;

                        //calculate latent heat to be removed
                        latent = 2500.8 - 2.36*temp_i + 0.0016*pow(temp_i,2) - 0.00006*pow(temp_i,3); //kJ/kg
                        Q = (remove_mass/1000)*latent; //(g * 1kg/1000g *kJ/kg) = kJ

                        //calculate and write final temp
                        temp_f = C_T(c,t) + Q/(c_crop*d_crop*C_VOLUME(c,t)); //kJ / kJ/kg*C * kg/m^3 * m^3 = C; +Q because heat is added
                        C_T(c,t) = temp_f;

                        // write to file the time step and location of condensation
                        if (file_write == 0){
                            FILE *fp;
                            fp = fopen("C:/Users/Rutgers/Desktop/David_Lewus_Research/CFD/Energy_Model_v3/condensation.txt", "a");
                            fprintf(fp, "%d %d\n", curr_ts, cell_ID[i]);
                            fclose(fp);
                            file_write = 1;
                        }

                    }
                }
                end_c_loop(c, t)
            }
        // for faces, look at adjacent cell to decide is condensation occurs there --> assume condensation happens at face surface based off activities in the cell
        for (int i = 0; i < 5; i++) //loops through each face zone
            {
                file_write = 0; // restart file_write to allow writing
                t = Lookup_Thread(d, face_ID[i]); //looks up thread for the face zone that's currently being worked on
                Message0("Zone ID = %d Thread = %d\n", face_ID[i], t);
                begin_f_loop(f, t)
                {
                // check if air is oversaturated with water vapor, i.e. RH > 100%
                    // look at neighboring cell, inside the tunnel
                    c0 = F_C0(f,t);
                    t0 = F_C0_THREAD(f,t);

                    // find saturation pressure and convert to H2O mass fraction
                    temp_i = C_T(c0,t0) - 273.15; //cell temp initial, C
                    e = 611*exp((17.27*temp_i)/(237.3+temp_i)); //saturation vapor pressure, Pa
                    pressure = C_P(c0,t0) + 101325; //adding 1atm to gauge pressure
                    dry_air_mass = (29 * (pressure - e)*C_VOLUME(c0,t0))/(8.314*temp_i); //g/mol * J/m3 * m3 * K*mol/J * 1/K , final unit is g
                    max_water_mass = (18 * e * C_VOLUME(c0,t0))/(8.314*temp_i); //maximum amount of water that can be held in the air at current temp
                    max_fraction = max_water_mass/(max_water_mass + dry_air_mass); //mass fraction with max amount of water held in air
                    //find species mass fraction, water-vapor is first species listed
                    mass_fraction_i = C_YI(c0, t0, 0);


                // condense on surface, if oversaturated, by removing water vapor from air and heating the surface
                    if (mass_fraction_i > max_fraction){
                        // water to be removed
                        water_mass_i = (mass_fraction_i * dry_air_mass)/(1 - mass_fraction_i);
                        remove_mass = water_mass_i - max_water_mass; // g
                        // set H2O mass fraction to max
                        C_YI(c0, t0, 0) = max_fraction;

                        //calculate latent heat to be removed
                        latent = 2500.8 - 2.36*temp_i + 0.0016*pow(temp_i,2) - 0.00006*pow(temp_i,3); //kJ/kg
                        Q = (remove_mass/1000)*latent; //(g * 1kg/1000g *kJ/kg) = kJ

                        //calculate and write final temp
                        temp_f = C_T(c0,t0) + Q/(c_plastic*d_plastic*C_VOLUME(c0,t0)); //kJ / kJ/kg*C * kg/m^3 * m^3 = C; +Q because heat is added
                        C_T(c0,t0) = temp_f;

                        // write to file the time step and location of condensation
                        if (file_write == 0){
                            FILE *fp;
                            fp = fopen("C:/Users/Rutgers/Desktop/David_Lewus_Research/CFD/Energy_Model_v3/condensation.txt", "a");
                            fprintf(fp, "%d %d\n", curr_ts, face_ID[i]);
                            fclose(fp);
                            file_write = 1;
                        }
                    }
                }
                end_f_loop(f, t)
            }
        }
}

DEFINE_EXECUTE_AT_END(evapotranspiration_v6_3_4_60s)
{
    int curr_ts;
    curr_ts = CURRENT_TIME;
    // this runs at the end of every 12 timesteps
    if (curr_ts % 60 == 0 ){
            //change 1st modulus and conversion directly after ET calculation for timestep size change

        Domain *d;
        d = Get_Domain(1);
        cell_t c;
        int ID [3]= {1099, 1111, 1096}; // Zone ID for fluid_medium_plant_1,2,3
        Thread *t;
        Thread *tf;
        float Rn;
        float Rs;
        float Rl;
        float sbc;
        float G;
        float gamma = 0.0647;
        float temp_i;
        float temp_f;
        float u;
        float v;
        float w;
        float u_2;
        float delta;
        float e;
        float e_a;
        float ET;
        int n;
        face_t f;
        float surface_area = 0;
        float latent;
        float Q;
        float c_crop = 3.2537; //kJ/kg*C
        float d_crop = 0.9*1000 + 0.1*1500; //kg/m^3
        real mass_fraction_i;
        real mass_fraction_f;
        real mass_var;
        real water_mass_i;
        real water_mass_f;
        real water_mass_add;
        real dry_air_mass;
        real pressure;
        real max_water_mass;
        real max_fraction;


        for (int i = 0; i < 3; i++) //loops through each cell zone
        {
            t = Lookup_Thread(d, ID[i]); //looks up thread for the cell zone that's currently being worked on
            Message0("Zone ID = %d Thread = %d\n", ID[i], t);
            begin_c_loop(c, t)
            {
                //read and calculate variables
                temp_i = C_T(c,t) - 273.15; //cell temp initial
                    //actual vapor pressure calculation
                mass_fraction_i = C_YI(c, t, 0);//find species mass fraction, water-vapor is first species listed
                    /*
                    mass fraction = mass of water/(mass of water + mass of dry air)
                    mass fraction*mass of water + mass fraction*mass of dry air = mass of water
                    mass fraction*mass of dry air = mass of water (1-mass fraction)
                    mass of water = (mass fraction * mass of dry air)/(1-mass fraction)
                    PV = nRT = (m/MW) * RT
                    m/MW = PV/RT
                    mass of dry air = MW_dry_air * PV/RT
                    e_a = nRT/V = mass_of_water/MW_water * RT/V
                        = (mass fraction * MW_dry_air * PV/RT)/((1-mass fraction)*MW_water) * RT/V
                        = (mass fraction * MW_dry_air * P)/((1-mass fraction)*MW_water)
                            P = P_tot - e_a
                    var = (mass fraction * MW_dry_air)/((1-mass fraction)*MW_water)
                    e_a = P * var = P_tot * var - e_a * var
                    e_a + e_a * var = P_tot * var
                    e_a (1 + var) = P_tot * var
                    e_a = (P_tot * var) / (1 + var)
                    */
                mass_var = (mass_fraction_i * 29)/((1-mass_fraction_i)*18);
                pressure = C_P(c,t) + 101325; //adding 1atm to gauge pressure
                e_a = (pressure * mass_var)/(1+mass_var); // Pa
                e = 611*exp((17.27*temp_i)/(237.3+temp_i)); //saturation vapor pressure, Pa


                    //Rn is the difference between incoming net shortwave and outgoing net longwave
                    //net shortwave is difference between incoming and reflected solar radiation (accounts for reflection)
                    //net longwave needs to account for absorbers and emitters of longwave radiation (water vapor, clouds, CO2, etc.)
                Rs = C_DO_IRRAD(c, t,0); // incident shortwave radiation in W/m^2
                sbc = 5.670374419e-8; //Stefan-Boltzmann constant in W/m^2
                Rl = sbc * pow(C_T(c,t), 4) * (0.34 - 0.14*(pow((e_a/1000),0.5))); //net longwave radiation in w/m^2: Stefan-Boltzmann law with correction for air humidity reflecting radiation
                Rn = Rs - Rl;
                Rn = (Rn*60)/1000000; //convert to MJ/(min*m^2)
                G = (soilheatflux*60)/1000000; //soil-heat flux from above profile, convert from w/m^2 to MJ/(min*m^2)



                u = C_U(c,t); //x wind velocity
                v = C_V(c,t); //y wind velocity
                w = C_W(c,t); //z wind velocity

                u_2 = pow(u,2) + pow(v,2) + pow(w,2);
                u_2 = pow(u_2,0.5); //velocity magnitude

                delta = 4098 * (0.6108 * exp((17.27 * temp_i)/(temp_i+237.3)))/pow((temp_i+237.3),2); //slope of saturation vapor pressure curve

                //calculate evapotranspiration
                ET = ((0.408*delta*(Rn-G)) + (gamma*(.625/(temp_i+273))*u_2*((e-e_a)/1000))) / (delta + gamma*(1+0.34*u_2)); //Penman-Monteith equation, divide e-e_a by 1000 to convert to kPa
                ET /= 1000; //convert from mm to m, final unit is m/min
                //ET *= (5/3); //convert from m/min to m/100s --> this is the only conversion necessary for a timestep size change

                if (ET > 0){
                //only calculate if ET is positive
                //calculate surface area
                    surface_area = 0; //reset surface area
                    c_face_loop(c,t,n)
                    {
                        real NV_VEC(area);
                        f = C_FACE(c,t,n);
                        tf = C_FACE_THREAD(c,t,n);
                        F_AREA(area,f,tf);
                        surface_area += NV_MAG(area);
                    }


                    //calculate water vapor being added to air
                        //ET*surface_area is m^3/min of water * density of water (1000kg/m^3) * 1000g/kg = g/min
                    water_mass_add = ET*surface_area*1000*1000;
                        //convert mass fraction to mass of water in air
                    dry_air_mass = (29 * (pressure - e_a)*C_VOLUME(c,t))/(8.314*C_T(c,t)); //g/mol * J/m3 * m3 * K*mol/J * 1/K , final unit is g
                    water_mass_i = (mass_fraction_i * dry_air_mass) / (1 - mass_fraction_i);
                        //add mass of water from transpiration to mass already in air
                    water_mass_f = water_mass_i + water_mass_add; //g/min * 1min = g, assuming this code is only called every minute
                        //convert new mass of water in air to mass fraction
                    mass_fraction_f = water_mass_f/(water_mass_f + dry_air_mass);

                        //make sure this volume of water is possible to add to the air
                    /*
                    PV = nRT
                    m/MW = PV/RT = eV/RT
                    m = MW*eV/RT
                    */
                    max_water_mass = (18 * e *C_VOLUME(c,t))/(8.314*C_T(c,t)); //maximum amount of water that can be held in the air at current temp
                    max_fraction = max_water_mass/(max_water_mass + dry_air_mass); //mass fraction with max amount of water held in air

                    if (mass_fraction_f > max_fraction){
                        mass_fraction_f = max_fraction;
                        water_mass_add = max_water_mass - water_mass_i;
                        if (water_mass_add < 0){
                            water_mass_add = 0; // this stops negative water mass being added, so condensation function can remove water
                        }
                    }

                        //overwrite mass fraction of water in air
                    C_YI(c, t, 0) = mass_fraction_f;


                    //calculate latent heat
                    latent = 2500.8 - 2.36*temp_i + 0.0016*pow(temp_i,2) - 0.00006*pow(temp_i,3); //kJ/kg
                    Q = (water_mass_add/1000)*latent; //(g/min * 1kg/1000g *kJ/kg) = kJ/min


                    //calculate and write final temp
                    temp_f = C_T(c,t) - Q/(c_crop*d_crop*C_VOLUME(c,t)); //kJ/min / kJ/kg*C * kg/m^3 * m^3 = C/min
                    C_T(c,t) = temp_f;
                }
            }
            end_c_loop(c, t)
        }
    }
}

DEFINE_PROPERTY(constant_density, c, t)
{
    real rho;
    rho = 1.225;
    return rho;
}
