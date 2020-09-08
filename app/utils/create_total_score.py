import pandas as pd 
import numpy as np 
from utils import zebra 
import os
import yaml 

with open("config.yml") as config_file: 
     config = yaml.load(config_file, Loader=yaml.FullLoader)

def create_total_score_excel(export_path, geo_weights_pivot, needs_weights_pivot, challenge_weights_pivot, stage_weights_pivot):
    ''' This function will create the total_score.xlsx
    sheet from the uploaded files
    '''
    # print("total score export_path: ", export_path)
    # Mentor data
    partners_df = zebra.csv_to_df(export_path+"partner_data.csv")
    # filled nan with 0 
    partners_df = partners_df.fillna(0)
    type(partners_df["Org"])

    # Solver data
    solver_df = zebra.csv_to_df(export_path+"solver_team_data.csv")
    # filled nan with 0 
    solver_df = solver_df.fillna(0)

    # Get geo choice for solver
    solver_geo = zebra.solver_geo_df(solver_df)

    # Get geo choices for partner
    partners_geo = zebra.partner_geo_df(partners_df)

    # Generate geo contingency table
    unpivoted_solver_geo = zebra.solver_regions_listform(solver_geo, solver_df)

    # Generate pivot table
    _,geo_pivot_copy = zebra.pivot_table_geo(unpivoted_solver_geo,partners_geo, export_path, export=True)

    # Get needs for Partners
    partners_needs = zebra.get_partners_needs(partners_df)

    # Get needs for Solveras
    unpivoted_solver_needs= zebra.get_solver_needs(solver_df)

    # Read in partner pivot table
    needs_values, needs_pivot_copy = zebra.pivot_table_needs(unpivoted_solver_needs,partners_needs, export_path, export=True)

    # Get Partner Challenges
    ch_partners_challenges = zebra.get_ch_partners(partners_df)

    # Get Solver Challenges
    ch_solver = zebra.get_ch_solvers(solver_df)

    # Generate pivot table
    challenges_pivot, challenges_pivot_copy = zebra.pivot_table_challenges(ch_solver, ch_partners_challenges, export_path, export=True)

    # Get Parter stage data
    st_partners = zebra.get_st_partners(partners_df)

    # Get Solver statge data
    st_solver = zebra.get_st_solver(solver_df)

    # Generate pivot table
    _,stage_pivot_copy = zebra.pivot_table_stage(st_solver, st_partners, export_path, export=True)

 
    geo_term = pd.DataFrame(geo_weights_pivot.values*geo_pivot_copy.astype(float).values, columns=geo_weights_pivot.columns, index=geo_weights_pivot.index)['geo_weights']
    stage_term = pd.DataFrame(stage_weights_pivot.values*stage_pivot_copy.astype(float).values, columns=stage_weights_pivot.columns, index=stage_weights_pivot.index)
    geo_stage_term = 100*pd.DataFrame(geo_term.values*stage_term.values, columns=stage_term.columns, index=stage_term.index)['stage_weights']
    needs_term =  pd.DataFrame(needs_weights_pivot.values*needs_pivot_copy.astype(float).values, columns=needs_weights_pivot.columns, index=needs_weights_pivot.index)['needs_weights']
    challenge_term = 10*pd.DataFrame(challenge_weights_pivot.values*challenges_pivot_copy.astype(float).values, columns=challenge_weights_pivot.columns, index=challenge_weights_pivot.index)['challenge_weights']

    # Combine all of the answers
    total_score = geo_stage_term + challenge_term + needs_term

    # Export to total_score.xlsx
    # total_score.to_excel("MIT_SOLVE_downloadable_excel_files/total_score_from_upload.xlsx")
    total_score.to_excel(export_path+"/total_score_from_upload.xlsx")

    return total_score