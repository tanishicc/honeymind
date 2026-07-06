# HoneyMind 🐝
## Building an AI-Powered Deception Honeypot from Scratch

### Why I Built This

I wanted to explore a question:

> Can a lightweight language model be used to create a believable deception environment that interacts with attackers and eventually learns from real-world attacker behaviour?

As someone interested in both cybersecurity and machine learning, I wanted a project that sat at the intersection of both fields.

---

# The Journey

## Phase 1 – The Idea

**Goal:**

Create an AI-powered terminal that could:

- simulate Linux systems
- deceive attackers
- collect attacker telemetry
- eventually improve itself using real attack data

Initially, I thought I could simply fine-tune a model on terminal commands and responses.

I quickly learned it was much harder than that.

---

## Phase 2 – First Dataset

I created:

deception_training_v1.jsonl

The model learned a few commands:

- whoami
- pwd
- ls

but failed badly on anything more complex.

Outputs became inconsistent and unrealistic.

---

## Phase 3 – Bigger Datasets

I experimented with:

- v2
- v3_balanced
- v4
- v5_task_conditioned
- v6_variations
- v7_targeted
- v8_repair
- v9_replay

Each version tried to solve a different problem:

| Version | Goal |
|---------|------|
| v3 | Balance command distribution |
| v4 | Add more realistic environments |
| v5 | Task-conditioned prompts |
| v6 | Massive dataset with command variations |
| v7 | Targeted fixes |
| v8 | Repair failed commands |
| v9 | Replay learning to prevent forgetting |

---

## Phase 4 – Learning About Machine Learning

I encountered several real ML challenges.

### Catastrophic Forgetting

Fixing one command often broke others.

Example:

pwd

became

bash: cd admin

### Overfitting

Models memorised command patterns instead of generalising.

### Continual Learning Challenges

Replay training helped, but also introduced new failures.

---

# Benchmark Results

| Model | Score |
|-------|--------|
| v5 | ~70% |
| v6 | ~70% |
| v8 | unstable |
| v9 | 57% |

After many experiments, I concluded:

> TinyLlama + synthetic fine-tuning is not enough to perfectly emulate Linux systems.

But it is good enough to build an intelligent deception environment.

---

# Final Architecture

Internet Attacker
↓
HoneyMind Terminal
↓
Fine-Tuned TinyLlama (v6)
↓
Session Logging
↓
Attacker Profiling Engine
↓
Future Behaviour Models

---

# What HoneyMind Can Do Today

✅ Simulate Linux environments

✅ Generate realistic terminal responses

✅ Log attacker sessions

✅ Profile attacker behaviour

✅ Assign risk scores

✅ Support dozens of attacker commands

---

# What It Cannot Do Yet

❌ Perfect Linux emulation

❌ Support every shell command

❌ Replace traditional honeypots

---

# The Most Important Lesson

The most valuable part of this project was not achieving perfect accuracy.

It was learning:

- dataset engineering
- LoRA fine-tuning
- continual learning
- evaluation and benchmarking
- the limitations of small language models
- how deception systems can evolve using real attacker data

---

# Future Vision

Deploy publicly
↓
Collect real attacker interactions
↓
Train behavioural models
↓
Predict attacker intent
↓
Build adaptive cyber defences

---

# Tech Stack

- Python
- TinyLlama
- HuggingFace Transformers
- PEFT / LoRA
- PyTorch
- JSONL Datasets

---

# Project Status

🚧 Active Research Project

This repository documents the ongoing development of HoneyMind and serves as both a portfolio project and a research experiment into AI-powered deception systems.

---

# Author

**Tanishi Jhalani**

Master of Cybersecurity  
Monash University  
Cybersecurity | AI | Deception Engineering

