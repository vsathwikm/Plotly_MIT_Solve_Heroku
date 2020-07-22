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

# for each row starting at index 2 we need to look at each column index 4-35 and find keyword 'match'
# iterate through every row
mentor_matches_dict = {}
for i in range(1,59):
    row = matches_df.iloc[i][4:36]
    mentor = matches_df.iloc[i][0]
    solver_matches = []
    for j in range(0,32):
        potential_match = str(row.iloc[j])
        if potential_match == 'Match' or potential_match == 'Match?':
            solver = matches_df.columns[j+4]
            solver_matches.append(solver)
    mentor_matches_dict[mentor] = solver_matches

for mentor in mentor_matches_dict:
    print("Mentor: " + str(mentor))
    print(len(mentor_matches_dict[mentor]))




