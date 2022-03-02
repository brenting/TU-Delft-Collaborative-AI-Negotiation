import json
import os
import time

from utils.plot_trace import plot_trace
from utils.runners import run_session

RESULTS_DIR = f"results/{time.strftime('%Y%m%d-%H%M%S')}"

# create results directory if it does not exist
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

# Settings to run a negotiation session:
#   We need to specify the classpath of 2 agents to start a negotiation.
#   We need to specify the preference profiles for both agents. The first profile will be assigned to the first agent.
#   We need to specify a deadline of amount of rounds we can negotiate before we end without agreement
settings = {
    "agents": [
        "agents.random_agent.random_agent.RandomAgent",
        "agents.template_agent.template_agent.TemplateAgent",
    ],
    "profiles": ["domains/domain00/profileA.json", "domains/domain00/profileB.json"],
    "deadline_rounds": 200,
}

# run a session and obtain results in dictionaries
results_trace, results_summary = run_session(settings)

# plot trace to html file
plot_trace(results_trace, f"{RESULTS_DIR}/trace_plot.html")

# write results to file
with open(f"{RESULTS_DIR}/results_trace.json", "w") as f:
    f.write(json.dumps(results_trace, indent=2))
with open(f"{RESULTS_DIR}/results_summary.json", "w") as f:
    f.write(json.dumps(results_summary, indent=2))
