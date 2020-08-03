import pandas as pd 
import numpy as np 
import zebra 
import os

def create_total_score_excel():
    ''' This function will create the total_score.xlsx
    sheet from the uploaded files
    '''

    # Mentor data
    partners_df = zebra.csv_to_df("partner_data.csv")
    # filled nan with 0 
    partners_df = partners_df.fillna(0)
    type(partners_df["Org"])

    # Solver data
    solver_df = zebra.csv_to_df("solver_team_data.csv")
    # filled nan with 0 
    solver_df = solver_df.fillna(0)

    # Get geo choice for solver
    solver_geo = zebra.solver_geo_df(solver_df)

    # Get geo choices for partner
    partners_geo = zebra.partner_geo_df(partners_df)

    # Generate geo contingency table
    unpivoted_solver_geo = zebra.solver_regions_listform(solver_geo, solver_df)

    # Generate pivot table
    _,geo_pivot_copy = zebra.pivot_table_geo(unpivoted_solver_geo,partners_geo,export=False)

    # Get needs for Partners
    partners_needs = zebra.get_partners_needs(partners_df)

    # Get needs for Solveras
    unpivoted_solver_needs= zebra.get_solver_needs(solver_df)

    # Read in partner pivot table
    needs_values, needs_pivot_copy = zebra.pivot_table_needs(unpivoted_solver_needs,partners_needs,export=False)

    # Get Partner Challenges
    ch_partners_challenges = zebra.get_ch_partners(partners_df)

    # Get Solver Challenges
    ch_solver = zebra.get_ch_solvers(solver_df)

    # Generate pivot table
    challenges_pivot, challenges_pivot_copy = zebra.pivot_table_challenges(ch_solver, ch_partners_challenges)

    # Get Parter stage data
    st_partners = zebra.get_st_partners(partners_df)

    # Get Solver statge data
    st_solver = zebra.get_st_solver(solver_df)

    # Generate pivot table
    _,stage_pivot_copy = zebra.pivot_table_stage(st_solver, st_partners)

    # Combine all of the answers
    total_score = ((geo_pivot_copy.astype(int)*stage_pivot_copy.astype(int))*100) + (challenges_pivot_copy.astype(int)*10 ) + needs_pivot_copy

    # Export to total_score.xlsx
    total_score.to_excel("total_score_from_upload.xlsx")



    return total_score