import pstats
import sys

p = pstats.Stats(sys.argv[1])
p.strip_dirs().sort_stats('cumtime').print_stats()
