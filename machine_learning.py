import pandas as pd
import xlrd

loc = "Solver Partnership Matching, Campaign #2.xlsx"

all_matches_df = pd.read_excel(loc,
header=0,
index_col=False,
keep_default_na=True
)

matches_df = all_matches_df[0:59].fillna(0)
#print(matches_df)

# will be a dictionary containing all the matches for each mentor
mentor_matches_dict = {}

# iterate through each row
for i in range(1,59):
    row = matches_df.iloc[i][4:36]
    mentor = matches_df.iloc[i][0]
    solver_matches = []
    # iterate through all cells within the row
    for j in range(0,32):
        potential_match = str(row.iloc[j])
        # check if a match
        if potential_match == 'Match' or potential_match == 'Match?':
            solver = matches_df.columns[j+4]
            solver_matches.append(solver)
    mentor_matches_dict[mentor] = solver_matches

# prints out dict to check
for mentor in mentor_matches_dict:
    print("Mentor: " + str(mentor))
    print(len(mentor_matches_dict[mentor]))




