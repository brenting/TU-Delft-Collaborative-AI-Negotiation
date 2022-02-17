import json
import os
import random

from utils.plot_trace import plot_trace
from utils.runners import run_session

# create results directory if it does not exist
if not os.path.exists("results"):
    os.mkdir("results")

# Settings to run a negotiation session:
#   We need to specify the classpath of 2 agents to start a negotiation.
#   We need to specify the preference profiles for both agents. The first profile will be assigned to the first agent.
#   We need to specify a deadline of amount of rounds we can negotiate before we end without agreement

rand_x = random.randint(0,9)
rand_agent = random.choice([
    "agents.agents.agent_one.AgentOne",
    "agents.boulware_agent.boulware_agent.BoulwareAgent",
    "agents.template_agent.template_agent.TemplateAgent",
    "agents.conceder_agent.conceder_agent.ConcederAgent",
    "agents.hardliner_agent.hardliner_agent.HardlinerAgent"
])

settings = {
    "agents": [
        "agents.agents.agent_one.AgentOne",
        rand_agent
    ],
    "profiles": [f"domains/domain0{rand_x}/profileA.json", f"domains/domain0{rand_x}/profileB.json"],
    "deadline_rounds": 200
}

# run a session and obtain results in dictionaries
results_trace, results_summary = run_session(settings)

# plot trace to html file
plot_trace(results_trace, "results/trace_plot.html")

# write results to file
with open("results/results_trace.json", "w") as f:
    f.write(json.dumps(results_trace, indent=2))
with open("results/results_summary.json", "w") as f:
    f.write(json.dumps(results_summary, indent=2))
