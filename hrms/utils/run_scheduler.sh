#!/bin/bash
# go to your bench directory
cd /home/frappe/frappe-bench/frappe-bench

# run your Python scheduler via bench
/home/frappe/.local/bin/bench --site hrms.localhost execute hrms.utils.scheduler_runner.run
