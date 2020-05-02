#!/bin/bash
for i in {1..22..4}; do
  let j=i+4
  echo -e "\nRANGE $i $j\n"
  /usr/bin/python3 "/mnt/c/Users/meow/OneDrive/College/Carnegie_Mellon/Spring 2020/Capstone/Repo/capstone-project/Simulator+Localizer/nba localizer.py" $i $j &
  done
done 2>/dev/null
# let i=4
# let j=i+4
# echo -e "\nRANGE $i $j\n"
# /usr/bin/python3 "/mnt/c/Users/meow/OneDrive/College/Carnegie_Mellon/Spring 2020/Capstone/Repo/capstone-project/Simulator+Localizer/nba localizer.py" $i $j &
# wait
# done