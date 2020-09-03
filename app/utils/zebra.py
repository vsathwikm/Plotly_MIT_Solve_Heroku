import pandas as pd 
import numpy as np

# path = '/media/pawan/e1/Data_science/colaberry/zebra/'
   
def csv_to_df(file_name): 
    """ Read a csv file and convert it to a pandas DataFrame
    :param file_name: Name of csv file
    :type file_name: string
    :return: DataFrame containing the data from file_name  
    :rtype: pandas.DataFrame
    """
    path_csv_folder = ''    
    csv_df = pd.read_csv(path_csv_folder+file_name)
    return csv_df 


def get_regions_dict(): 
    """ Arrange countries by MIT Solve defined regions

    :return: Dictionary containing MIT solver defined regions
    :rtype: dict
    """
    regions  = csv_to_df("regions.csv")
    grouped_regions = regions.groupby(by="Region")
    regions_dict = {}
    for group in grouped_regions: 
        regions_dict[group[0]] =  group[1]["Country"].tolist()

    return regions_dict



def solver_geo_df(solver_df):
    """Get solver geo preferences from the solver data partner data sheet

    :param solver_df: DataFrame containing the solver data sheet
    :type solver_df: pandas.core.frame.DataFrame
    :return: DataFrame contain geographical region preference for each solver
    :rtype: pandas.core.frame.DataFrame
    """
    geo_cols = solver_df.columns[solver_df.columns.str.contains("Geo")]
    solver_geo = solver_df[geo_cols.values].T
    solver_geo = solver_geo.rename(columns= solver_df['Org'])
    return solver_geo

def partner_geo_df(partners_df): 
    """ Get partner geographical region preferences from partners data sheet

    :param partners_df:DataFrame containing the partners data sheet
    :type partners_df: pandas.core.frame.DataFrame
    :return: DataFrame contain geographical region preference for each partner
    :rtype: pandas.core.frame.DataFrame
    """
    partners_geo = partners_df["Geo Interests"].to_frame()
    partners_geo= partners_geo.rename(index=partners_df["Org"])

    partners_geo["Geo Interests"] = partners_geo["Geo Interests"].str.split(',')
    partners_geo = partners_geo.explode("Geo Interests")
    grouped_partners = partners_geo.groupby(by="Geo Interests")
    region_to_partners ={}
    for x in grouped_partners: 
        region_to_partners[x[0]] = x[1].index
    partners_geo = partners_geo.reset_index().rename(columns={'index':'Org'})

    return partners_geo

def solver_regions_listform(solver_geo, solver_df):
    """ Convert the solver_geo DataFrame from a contingency table to a list form

    :param solver_geo: DataFrame contain geographical region preference for each solver 
    :type solver_geo: pandas.core.frame.DataFrame 
    :param solver_df: DataFrame contain the solver teams data
    :type solver_df: pandas.DataFrame
    :return: Dataframe that results geographical preferences in list form 
    :rtype: pandas.core.frame.DataFrame
    """
    solver_geo = solver_geo.rename(columns= solver_df["Org"]) 
    solver_geo_reset = solver_geo.reset_index() 
    solver_geo_reset =solver_geo_reset.rename(columns= {'index': 'geo'})
    unpivoted_solver_geo= pd.melt(solver_geo_reset,
                                   id_vars='geo',
                                    value_vars= solver_df["Org"],
                                    var_name='Org',
                                    value_name="match")
    unpivoted_solver_geo["geo"] = unpivoted_solver_geo["geo"].apply(lambda x: str(x.replace("Geo","")))
    unpivoted_solver_geo["geo_match"] = unpivoted_solver_geo["geo"] + ","+ unpivoted_solver_geo["match"].apply(lambda x: str(x))

    return unpivoted_solver_geo

def pivot_table_geo( unpivoted_solver_geo, partners_geo, export_path,  export=False):
    """ Generate a pivot table for geographical preferences

    :param unpivoted_solver_geo: List form data representing a solver team's geological preference
    :type unpivoted_solver_geo: pandas.core.frame.DataFrame
    :param partners_geo: List form of partners geographical preferences
    :type partners_geo: pandas.core.frame.DataFrame
    :param export: Export dataframe to a csv file with filename 'geo_match.xlsx', defaults to False
    :type export: bool, optional
    :return geo_pivot_values: The pivot table as a dataframe
    :rtype: pandas.core.frame.DataFrame
    :return geo_pivot_copy: A copy of the pivot table where zeros of string type are converted to int type
    :rtype: pandas.core.frame.DataFrame
    """
    
    merged_geo = pd.merge(unpivoted_solver_geo,
                          partners_geo,
                          left_on="match",
                          right_on = "Geo Interests",
                          how='outer')
    geo_pivot = pd.pivot_table(merged_geo,
                               index='Org_y',
                               columns='Org_x',
                               values='geo_match',
                               aggfunc=np.sum).fillna(0)
    geo_pivot_values =  pd.pivot_table(merged_geo,
                                       index='Org_y',
                                       columns='Org_x',
                                       values='geo',
                                       aggfunc=np.sum).fillna(0)
    

    geo_pivot_copy = geo_pivot_values.copy()
    for col in geo_pivot_copy.columns: 
        geo_pivot_copy[col] = geo_pivot_copy[col].astype(str)
        geo_pivot_copy[col] = geo_pivot_copy[col].apply(lambda x: 0 if x.strip()== '0' else len(x.split()))
                                          
    if export==True: 
        geo_pivot_copy.to_excel("".join([export_path, "/geo_match.xlsx"]))

    return geo_pivot_values, geo_pivot_copy 


def clean_needs(df, col, clean_phrases):
    """ Remove words from a DataFrame element

    :param df: DataFrame whose elements have to be cleaned
    :type df: pandas.core.frame.DataFrame
    :param col: Column in the DataFrame 
    :type col: str
    :param clean_phrases: list of phrases to be removed from each element
    :type clean_phrases: list 
    :return: DataFrame column where phrases have been removed
    :rtype: pandas.core.series.Series
    """
    for phrase in clean_phrases:  
        df[col] = df[col].apply(lambda x:  phrase if phrase in x  else x  )
    return df[col]

def get_partners_needs(partners_df):
    """ Get partner preferences from the partners DataFrame 

    There are multiple data cleaning steps here, special symbols are removed, 
    and a list of words are also removed from Needs columns, this is done better 
    match the partner needs with solver needs
    
    :param partners_df: DataFrame containing partners preference data
    :type partners_df: pandas.core.frame.DataFrame
    :return: A DataFrame containing partner needs, this is unpivoted data
    :rtype: pandas.core.frame.DataFrame
    """
    partners_needs = partners_df[["Org", "Partnership Preference: Non-Financial"]]
    partners_needs = partners_needs.rename(columns={"Partnership Preference: Non-Financial": "Needs"})
    partners_needs["Needs"] = partners_needs["Needs"].str.replace(r"\([^)]*\)","")
    partners_needs["Needs"] = partners_needs["Needs"].apply(lambda x: str(x).strip().split(","))
    partners_needs = partners_needs.explode(column="Needs")
    partners_needs = partners_needs.reset_index().drop("index", axis=1)
    partners_needs["Needs"] = partners_needs["Needs"].str.strip()
    partners_needs["Needs"] = clean_needs(partners_needs, "Needs",
                                             ["Financial", "Distribution", "Technology"])                                        
    partners_needs["Needs"] = partners_needs["Needs"].str.strip()
    
    return partners_needs


def get_solver_needs(solver_df):
    """ Get solver needs columns from the solver DataFrame

    :param solver_df: DataFrame contain the solver teams data
    :type solver_df: pandas.core.frame.DataFrame
    :return: An unpivoted table of solver needs
    :rtype: pandas.core.frame.DataFrame
    """
    needs_cols = solver_df.columns[solver_df.columns.str.contains("Key")]
    solver_needs = solver_df[needs_cols.values].T
    solver_needs = solver_needs.rename(columns= solver_df["Org"])
    solver_needs = solver_needs.reset_index().rename(columns={"index":"key_needs"})
    unpivoted_solver_needs = pd.melt(solver_needs,
                                    id_vars="key_needs",
                                    value_vars=solver_df["Org"], 
                                    value_name="match",
                                    var_name="Org" )
    unpivoted_solver_needs["key_needs"] = unpivoted_solver_needs["key_needs"].apply(lambda x: x.replace("Key Need","").strip())
    unpivoted_solver_needs["needs_match"] = unpivoted_solver_needs["key_needs"]+","+unpivoted_solver_needs["match"].astype(str) 
    unpivoted_solver_needs["match"].value_counts()
    unpivoted_solver_needs["match"] = unpivoted_solver_needs["match"].str.split(",")
    unpivoted_solver_needs = unpivoted_solver_needs.explode(column="match")
    unpivoted_solver_needs["match"] = unpivoted_solver_needs["match"].astype(str)
    return unpivoted_solver_needs



def pivot_table_needs(unpivoted_solver_needs, partners_needs, export_path,  export=False): 
    """ Generate the pivot table for solver-partner needs 

    :param unpivoted_solver_needs: An unpivoted table of solver needs
    :type unpivoted_solver_needs: pandas.core.frame.DataFrame
    :param partners_needs: A DataFrame containing partner needs, this is unpivoted data
    :type partners_needs: pandas.core.frame.DataFrame
    :param export: Export dataframe to a csv file with filename 'needs_match.xlsx', defaults to False
    :type export: bool, optional
    :return needs_pivot_values: The pivot table as a dataframe
    :rtype: pandas.core.frame.DataFrame
    :return needs_pivot_copy: A copy of the pivot table where zeros of string type are converted to int type
    :rtype: pandas.core.frame.DataFrame
    """
    merged_needs = pd.merge(unpivoted_solver_needs,
                            partners_needs,
                            left_on="match",
                            right_on="Needs",
                            how="outer")
    needs_pivot = pd.pivot_table(merged_needs,
                                index="Org_y",
                                columns="Org_x",
                                values="needs_match",
                                aggfunc=np.sum)
    
    need_pivot_values = pd.pivot_table(merged_needs,
                                       index="Org_y",
                                       columns="Org_x",
                                       values="key_needs",
                                       aggfunc=np.sum)
    need_pivot_values = need_pivot_values.fillna(0)
    need_pivot_copy = need_pivot_values.copy()
   
    for col in need_pivot_copy.columns:     
        need_pivot_copy[col] = need_pivot_copy[col].apply(lambda x: 0 if len(str(x))>4 or x == 0 else len(str(x))) 

    if export == True: 
        need_pivot_copy.to_excel("".join([export_path,"/needs_match.xlsx"]))

    return  need_pivot_values, need_pivot_copy




def get_ch_partners(partners_df): 
    """ Get challenge preferences for partners 

    :param partners_df: DataFrame containing partners preference data
    :type partners_df: pandas.core.frame.DataFrame
    :return: An unpivoted list of partner preferences
    :rtype: pandas.core.frame.DataFrame
    """
    ch_partners = partners_df[["Org","Challenge Preference"]]
    ch_partners["Challenge Preference"] =  ch_partners["Challenge Preference"].str.split(",")
    ch_partners_explode = ch_partners.explode("Challenge Preference")
    ch_partners_explode = ch_partners_explode.rename(columns={"Challenge Preference": "Challenge"})
    ch_partners_explode = ch_partners_explode.apply(lambda x: x.str.strip())
    ch_partners_explode.Challenge.astype(str)
    ch_partners_reset = ch_partners_explode.reset_index().drop('index', axis=1)
    ch_partners_reset["Org"] = ch_partners_reset["Org"].astype(str)
    
    return ch_partners_reset 

def get_ch_solvers(solver_df):
    """ Get DataFrame of solver preferences 

    :param solver_df:  DataFrame contain the solver teams data
    :type solver_df: pandas.core.frame.DataFrame
    :return: An unpivoted list of solver preferences
    :rtype: pandas.core.frame.DataFrame
    """
    ch_solver = solver_df[["Org", "Challenge"]]
    ch_solver = ch_solver.apply(lambda x: x.str.strip() )
    ch_solver["Org"] = ch_solver["Org"].astype(str)
    
    return ch_solver


def pivot_table_challenges(ch_solver, ch_partners_reset, export_path, export=False):
    """ Generate the challenges pivot table

    :param ch_solver: An unpivoted list of solver preferences
    :type ch_solver: pandas.core.frame.DataFrame
    :param ch_partners_reset: An unpivoted list of partner preferences
    :type ch_partners_reset: pandas.core.frame.DataFrame
    :param export: Export dataframe to a csv file with filename 'challenge_match.xlsx', defaults to False
    :type export: bool, optional
    :return challenges_pivot: The pivot table as a dataframe
    :rtype: pandas.core.frame.DataFrame
    :return challenges_pivot_copy: A copy of the pivot table where each element will be set to 1 if not 0 
    :rtype: pandas.core.frame.DataFrame
    """
    merged_df = pd.merge(ch_solver,
                         ch_partners_reset,
                         left_on="Challenge",
                         right_on='Challenge',
                         how='outer')
    merged_pivot_table = pd.pivot_table(merged_df,
                                        values="Challenge",
                                        index=["Org_y"],
                                        columns=["Org_x"],
                                        aggfunc=np.sum)
    
    
    challenges_pivot = merged_pivot_table.copy()
    challenges_pivot = challenges_pivot.fillna(0)
    challenges_pivot_nulled = challenges_pivot.isnull()
    
    for col in challenges_pivot_nulled.columns: 
        challenges_pivot_nulled[col] = challenges_pivot_nulled[col].apply(lambda x: 0 if x is True else 1)
    challenges_pivot_copy = challenges_pivot_nulled.copy()

    if export == True:
        challenges_pivot_copy.to_excel("".join([export_path, "challenge_match.xlsx"]))
    
    return challenges_pivot, challenges_pivot_copy



def get_st_partners(partners_df): 
    """ Get Stage preference for partners 

    :param partners_df: DataFrame containing partners preference data
    :type partners_df: pandas.core.frame.DataFrame
    :return: An unpivoted DataFrame of partner preferences
    :rtype: pandas.core.frame.DataFrame
    """
    st_partners = partners_df[["Org","Solution Preference: Organization Stage"]]
    st_partners["Stage"] = st_partners["Solution Preference: Organization Stage"].str.strip()
    st_partners["Stage"] = st_partners["Stage"].str.split(",")
    st_partners = st_partners.drop("Solution Preference: Organization Stage", axis=1)
    st_partners = st_partners.explode("Stage")
    st_partners_reset = st_partners.reset_index().drop('index', axis=1)
    st_partners_reset
    
    return st_partners_reset

def get_st_solver(solver_df):
    """Get Stage preference for solvers
    
    :param solver_df: DataFrame contain the solver teams data
    :type solver_df: pandas.core.frame.DataFrame
    :return:  An unpivoted DataFrame of solver preferences
    :rtype: pandas.core.frame.DataFrame
    """
    st_solver = solver_df[["Org","Stage"]]
    st_solver["Stage"] = st_solver["Stage"].str.strip()
    
    return st_solver


def pivot_table_stage(st_solver, st_partners, export_path,  export=False):
    """ Generate the stage pivot table

    :param st_solver: An unpivoted DataFrame of solver preferences
    :type st_solver: pandas.core.frame.DataFrame
    :param st_partners: An unpivoted DataFrame of partner preferences
    :type st_partners: pandas.core.frame.DataFrame
    :param export:  Export dataframe to a csv file with filename 'stage_match.xlsx', defaults to False
    :type export: bool, optional
    :return stage_pivot: The pivot table as a dataframe
    :rtype: pandas.core.frame.DataFrame
    :return stage_pivot_copy: A copy of the pivot table where each element will be 0 if x is 0 else its 1 
    :rtype: pandas.core.frame.DataFrame
    """
    merged_st = pd.merge(st_solver,
                         st_partners,
                         left_on='Stage',
                         right_on='Stage',
                         how='outer')
    merged_st_ptable = pd.pivot_table(merged_st,
                                      values="Stage",
                                      index=["Org_y"],
                                      columns=["Org_x"],
                                      aggfunc=np.sum)
    #merged_st_ptable = merged_st_ptable.fillna(0).reset_index()
    merged_st_ptable = merged_st_ptable.fillna(0)

    
    stage_pivot = merged_st_ptable.copy()

    for col in stage_pivot.columns: 
        stage_pivot[col] = stage_pivot[col].apply(lambda x: 0 if x == 0 else 1 )

    stage_pivot = stage_pivot.rename(index=st_partners["Org"])
    stage_pivot_copy = stage_pivot.copy()
    #stage_pivot_copy = stage_pivot_copy.drop(labels="Org_y", axis=1)
    stage_pivot_copy

    if export == True: 
        stage_pivot_copy.to_excel("".join([export_path, "/stage_match.xlsx" ]))
    
    return stage_pivot, stage_pivot_copy


if __name__ == "__main__":
    print(get_regions_dict())

