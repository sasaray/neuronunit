COMMENT

   **************************************************
   File generated by: neuroConstruct v1.5.1 
   **************************************************

   This file holds the implementation in NEURON of the Cell Mechanism:
   CaT (Type: Channel mechanism, Model: ChannelML based process)

   with parameters: 
   /channelml/@units = SI Units 
   /channelml/notes = ChannelML file containing a single Channel description 
   /channelml/channel_type/@name = CaT 
   /channelml/channel_type/status/@value = stable 
   /channelml/channel_type/status/comment = Equations adapted from Kali 
   /channelml/channel_type/status/contributor/name = Bogl�rka Sz?ke 
   /channelml/channel_type/notes = Low-threshold Ca(T) Channel in pyramid neurons 
   /channelml/channel_type/authorList/modelTranslator/name = Bogl�rka Sz?ke 
   /channelml/channel_type/authorList/modelTranslator/institution = PPKE-ITK 
   /channelml/channel_type/authorList/modelTranslator/email = szoboce - at - digitus.itk.ppke.hu 
   /channelml/channel_type/current_voltage_relation/@cond_law = ohmic 
   /channelml/channel_type/current_voltage_relation/@ion = ca 
   /channelml/channel_type/current_voltage_relation/@charge = 2 
   /channelml/channel_type/current_voltage_relation/@default_gmax = 14.8 
   /channelml/channel_type/current_voltage_relation/@default_erev = 0.080 
   /channelml/channel_type/current_voltage_relation/@fixed_erev = yes 
   /channelml/channel_type/current_voltage_relation/gate[1]/@name = X 
   /channelml/channel_type/current_voltage_relation/gate[1]/@instances = 2 
   /channelml/channel_type/current_voltage_relation/gate[1]/closed_state/@id = X0 
   /channelml/channel_type/current_voltage_relation/gate[1]/open_state/@id = X 
   /channelml/channel_type/current_voltage_relation/gate[1]/transition[1]/@name = alpha 
   /channelml/channel_type/current_voltage_relation/gate[1]/transition[1]/@from = X0 
   /channelml/channel_type/current_voltage_relation/gate[1]/transition[1]/@to = X 
   /channelml/channel_type/current_voltage_relation/gate[1]/transition[1]/@expr_form = exponential 
   /channelml/channel_type/current_voltage_relation/gate[1]/transition[1]/@rate = 30 
   /channelml/channel_type/current_voltage_relation/gate[1]/transition[1]/@scale = 0.0234 
   /channelml/channel_type/current_voltage_relation/gate[1]/transition[1]/@midpoint = -0.017 
   /channelml/channel_type/current_voltage_relation/gate[1]/transition[2]/@name = beta 
   /channelml/channel_type/current_voltage_relation/gate[1]/transition[2]/@from = X 
   /channelml/channel_type/current_voltage_relation/gate[1]/transition[2]/@to = X0 
   /channelml/channel_type/current_voltage_relation/gate[1]/transition[2]/@expr_form = exponential 
   /channelml/channel_type/current_voltage_relation/gate[1]/transition[2]/@rate = 30 
   /channelml/channel_type/current_voltage_relation/gate[1]/transition[2]/@scale = -0.0234 
   /channelml/channel_type/current_voltage_relation/gate[1]/transition[2]/@midpoint = -0.017 
   /channelml/channel_type/current_voltage_relation/gate[2]/@name = Y 
   /channelml/channel_type/current_voltage_relation/gate[2]/@instances = 1 
   /channelml/channel_type/current_voltage_relation/gate[2]/closed_state/@id = Y0 
   /channelml/channel_type/current_voltage_relation/gate[2]/open_state/@id = Y 
   /channelml/channel_type/current_voltage_relation/gate[2]/transition[1]/@name = alpha 
   /channelml/channel_type/current_voltage_relation/gate[2]/transition[1]/@from = Y0 
   /channelml/channel_type/current_voltage_relation/gate[2]/transition[1]/@to = Y 
   /channelml/channel_type/current_voltage_relation/gate[2]/transition[1]/@expr_form = exponential 
   /channelml/channel_type/current_voltage_relation/gate[2]/transition[1]/@rate = 10 
   /channelml/channel_type/current_voltage_relation/gate[2]/transition[1]/@scale = -0.0136 
   /channelml/channel_type/current_voltage_relation/gate[2]/transition[1]/@midpoint = -0.071 
   /channelml/channel_type/current_voltage_relation/gate[2]/transition[2]/@name = beta 
   /channelml/channel_type/current_voltage_relation/gate[2]/transition[2]/@from = Y 
   /channelml/channel_type/current_voltage_relation/gate[2]/transition[2]/@to = Y0 
   /channelml/channel_type/current_voltage_relation/gate[2]/transition[2]/@expr_form = exponential 
   /channelml/channel_type/current_voltage_relation/gate[2]/transition[2]/@rate = 10 
   /channelml/channel_type/current_voltage_relation/gate[2]/transition[2]/@scale = 0.0136 
   /channelml/channel_type/current_voltage_relation/gate[2]/transition[2]/@midpoint = -0.071 
   /channelml/channel_type/impl_prefs/table_settings/@max_v = 0.05 
   /channelml/channel_type/impl_prefs/table_settings/@min_v = -0.1 
   /channelml/channel_type/impl_prefs/table_settings/@table_divisions = 3000 

// File from which this was generated: /home/kali/nC_projects/CA1_NEURON/cellMechanisms/CaT/CaT.xml

// XSL file with mapping to simulator: /home/kali/nC_projects/CA1_NEURON/cellMechanisms/CaT/ChannelML_v1.8.1_NEURONmod.xsl

ENDCOMMENT


?  This is a NEURON mod file generated from a ChannelML file

?  Unit system of original ChannelML file: SI Units

COMMENT
    ChannelML file containing a single Channel description
ENDCOMMENT

TITLE Channel: CaT

COMMENT
    Low-threshold Ca(T) Channel in pyramid neurons
ENDCOMMENT


UNITS {
    (mA) = (milliamp)
    (mV) = (millivolt)
    (S) = (siemens)
    (um) = (micrometer)
    (molar) = (1/liter)
    (mM) = (millimolar)
    (l) = (liter)
}


    
NEURON {
      

    SUFFIX CaT
    USEION ca WRITE ica VALENCE 2 ?  outgoing current is written
           
        
    RANGE gmax, gion, ica
    
    RANGE Xinf, Xtau
    
    RANGE Yinf, Ytau
    
}

PARAMETER { 
      

    gmax = 0.00148 (S/cm2)  ? default value, should be overwritten when conductance placed on cell
    
}



ASSIGNED {
      

    v (mV)
    
    celsius (degC)
          

    ? Reversal potential of ca
    eca (mV)
    ? The outward flow of ion: ca calculated by rate equations...
    ica (mA/cm2)
    
    
    gion (S/cm2)
    Xinf
    Xtau (ms)
    Yinf
    Ytau (ms)
    
}

BREAKPOINT { 
                        
    SOLVE states METHOD cnexp
         

    gion = gmax*((X)^2)*((Y)^1)      

    ica = gion*(v - eca)
            

}



INITIAL {
    
    eca = 80
        
    rates(v)
    X = Xinf
        Y = Yinf
        
    
}
    
STATE {
    X
    Y
    
}

DERIVATIVE states {
    rates(v)
    X' = (Xinf - X)/Xtau
    Y' = (Yinf - Y)/Ytau
    
}

PROCEDURE rates(v(mV)) {  
    
    ? Note: not all of these may be used, depending on the form of rate equations
    LOCAL  alpha, beta, tau, inf, gamma, zeta, temp_adj_X, A_alpha_X, B_alpha_X, Vhalf_alpha_X, A_beta_X, B_beta_X, Vhalf_beta_X, temp_adj_Y, A_alpha_Y, B_alpha_Y, Vhalf_alpha_Y, A_beta_Y, B_beta_Y, Vhalf_beta_Y
        
    TABLE Xinf, Xtau,Yinf, Ytau
 DEPEND celsius
 FROM -100 TO 50 WITH 3000
    
    
    UNITSOFF
    temp_adj_X = 1
    temp_adj_Y = 1
    
            
                
           

        
    ?      ***  Adding rate equations for gate: X  ***
        
    ? Found a parameterised form of rate equation for alpha, using expression: A*exp((v-Vhalf)/B)
    A_alpha_X = 30
    B_alpha_X = 0.0234
    Vhalf_alpha_X = -0.017   
    
    ? Unit system in ChannelML file is SI units, therefore need to convert these to NEURON quanities...
    
    A_alpha_X = A_alpha_X * 0.0010   ? 1/ms
    B_alpha_X = B_alpha_X * 1000   ? mV
    Vhalf_alpha_X = Vhalf_alpha_X * 1000   ? mV
          
                     
    alpha = A_alpha_X * exp((v - Vhalf_alpha_X) / B_alpha_X)
    
    
    ? Found a parameterised form of rate equation for beta, using expression: A*exp((v-Vhalf)/B)
    A_beta_X = 30
    B_beta_X = -0.0234
    Vhalf_beta_X = -0.017   
    
    ? Unit system in ChannelML file is SI units, therefore need to convert these to NEURON quanities...
    
    A_beta_X = A_beta_X * 0.0010   ? 1/ms
    B_beta_X = B_beta_X * 1000   ? mV
    Vhalf_beta_X = Vhalf_beta_X * 1000   ? mV
          
                     
    beta = A_beta_X * exp((v - Vhalf_beta_X) / B_beta_X)
    
    Xtau = 1/(temp_adj_X*(alpha + beta))
    Xinf = alpha/(alpha + beta)
          
       
    
    ?     *** Finished rate equations for gate: X ***
    

    
            
                
           

        
    ?      ***  Adding rate equations for gate: Y  ***
        
    ? Found a parameterised form of rate equation for alpha, using expression: A*exp((v-Vhalf)/B)
    A_alpha_Y = 10
    B_alpha_Y = -0.0136
    Vhalf_alpha_Y = -0.071   
    
    ? Unit system in ChannelML file is SI units, therefore need to convert these to NEURON quanities...
    
    A_alpha_Y = A_alpha_Y * 0.0010   ? 1/ms
    B_alpha_Y = B_alpha_Y * 1000   ? mV
    Vhalf_alpha_Y = Vhalf_alpha_Y * 1000   ? mV
          
                     
    alpha = A_alpha_Y * exp((v - Vhalf_alpha_Y) / B_alpha_Y)
    
    
    ? Found a parameterised form of rate equation for beta, using expression: A*exp((v-Vhalf)/B)
    A_beta_Y = 10
    B_beta_Y = 0.0136
    Vhalf_beta_Y = -0.071   
    
    ? Unit system in ChannelML file is SI units, therefore need to convert these to NEURON quanities...
    
    A_beta_Y = A_beta_Y * 0.0010   ? 1/ms
    B_beta_Y = B_beta_Y * 1000   ? mV
    Vhalf_beta_Y = Vhalf_beta_Y * 1000   ? mV
          
                     
    beta = A_beta_Y * exp((v - Vhalf_beta_Y) / B_beta_Y)
    
    Ytau = 1/(temp_adj_Y*(alpha + beta))
    Yinf = alpha/(alpha + beta)
          
       
    
    ?     *** Finished rate equations for gate: Y ***
    

         

}


UNITSON

