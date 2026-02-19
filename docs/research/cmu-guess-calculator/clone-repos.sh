#!/bin/bash
cd /Users/cdavis/github/password-cracking/cmu-guess-calculator

# Clone the three CMU CUPS Lab repos
git clone https://github.com/cupslab/guess-calculator-framework.git 2>&1
git clone https://github.com/cupslab/neural_network_cracking.git 2>&1
git clone https://github.com/cupslab/password_meter.git 2>&1

echo "--- Done cloning ---"
