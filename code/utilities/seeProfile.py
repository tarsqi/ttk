import pstats
import sys

profile = sys.argv[1]
p = pstats.Stats(profile)

# sorted on function name
#p.sort_stats('name').print_stats()

# Sort the profile by cumulative time in a function, and then only
# prints the top X of funcitons. To understand where most time is
# spent.
p.sort_stats('cumulative').print_stats(40)

# If you were looking to see what functions were looping a lot, and
# taking a lot of time, you would do:
#p.sort_stats('time').print_stats(25)

