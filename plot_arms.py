"""Draw the two arms as choice-vs-value-fraction. The finding IS a step function,
and a step function is a shape, so it gets looked at rather than described."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
Q = 1 / 3
ARMS = [("answers35_q3_nothink.json", "reasoning OFF", "#8a8f98"),
        ("answers35_q3_think.json", "reasoning ON", "#c2410c")]

fig, axes = plt.subplots(2, 1, figsize=(9, 5.2), sharex=True)
for ax, (fn, title, col) in zip(axes, ARMS):
    rows = [r for r in json.load(open(os.path.join(HERE, fn))) if r["chose"] is not None]
    ax.axvspan(0, Q, color="#f1f5f9", zorder=0)
    ax.axvline(Q, color="#0f172a", lw=1.1, ls="--", zorder=2)
    for r in rows:
        ax.plot([r["vf"]], [r["chose"]], "o", ms=7, mfc=col if r["chose"] else "none",
                mec=col, mew=1.4, zorder=3, alpha=0.9)
    n = len(rows)
    agree = sum(1 for r in rows if (r["chose"] == 1) == (r["vf"] < Q))
    ax.set_yticks([0, 1]); ax.set_yticklabels(["abstain", "participate"], fontsize=9)
    ax.set_ylim(-0.45, 1.45); ax.set_xlim(0, 1)
    ax.set_title(f"{title}   —   agrees with 'participate iff vf < 1/3' on {agree}/{n}",
                 fontsize=10.5, loc="left")
    ax.grid(axis="x", color="#e2e8f0", lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
axes[0].text(Q + 0.012, 1.22, "q = 1/3", fontsize=8.5, color="#0f172a")
axes[1].set_xlabel("agent_id as a fraction of its 128-bit range   (the model was never "
                   "told this quantity exists)", fontsize=9)
fig.suptitle("gemini-3.5-flash, same prompt, same 64 identifiers, reasoning toggled",
             fontsize=12, x=0.012, ha="left", weight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.94))
out = os.path.join(HERE, "arms_step.png")
fig.savefig(out, dpi=150)
print("wrote", out)
