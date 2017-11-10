# DitchDetConn
Scripts for the publication: Scripts for the publication: 'Extracting drainage networks and their connectivity using LiDAR data (under review)'. Only scripts containing a number need to be ran.

How to use these scripts? [In allignment with the publication]

1. Change input files and parameters in DetConn_Input script and save
2. Run DetConn_1_Detection
    - The appropriate files will be created
    - A preliminary ditch network will be extracted
    - The network will be merged with an existing digitized water network if available (input)
3. Run DetConn_2_Shift
    - Run this script to improve the positional accuracy from the preliminary ditch network using the underlying point cloud
    - The rest of the scripts can also be used without doing this step (under construction)
4. Run DetConn_3_PossConn
    - Possible connections in the shifted preliminary network will be detected
    - IMPORTANT: AFTER RUNNING THIS SCRIPT, UPDATE THE CONN ATTRIBUTE IN THE SHAPEFILE BASED ON FIELD DATA 
      (1 = True connection, 0 = False connection)
5. Run DetConn_4_ProbModel
    - The line and buffer characteristics of the possible connectiond will be extracted
    - These are then used as predictor variabled to calibrate a logistic connection probability model
    - Error metrics are calculated for the calibrated model
6. Run DetConn_5_Connect
    - The calibrated logistic connection model will be implemented on the overall network
    - It is possible to implement your own probability model (see script, form = True)
    - If you want to use the one developed in DetConn_4_ProbModel, write 'form = False)

Model code and parts of the code can be reused with attribution (see license file)

Roelens J. et al. (2017), Extracting drainage networks and their connectivity using LiDAR data, Hydrological Process (under review)

# I'm an environmental modeller, not a professional programmer
