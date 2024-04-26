# Overview
`evaluation/` contains Gobra files and scripts that can be used to
evaluate and plot, for example, the effect of using `opaque` in the
standard library or using the standard library on the execution time
and number of quantifier instantiations.

## `scripts/`
Contains scripts to
- measure execution time and the number of quantifier instantiations
and store the results in a csv file (`profile.py`)
- plot the data from one or more csv files (`plot.py`)
- profile and plot every file in `experiments/` (`profile-all.sh`)

### Dependencies and Usage
plot.py has the following dependencies:
- pandas
- numpy
- seaborn
- matplotlib
Install these packages using your favorite package manager
for Python packages (e.g., apt, pacman, nix, pip, conda, etc.).

profile.py requires the path to the following files:
- silicon.sh
- Z3 (version 4.8.7)
- Gobra jar
We have only tested Z3 4.8.7; newer versions may not work as they produce
errors and different output. Additionally, in case you get errors of
the form
```
    metadata["silicon_version"] = command_stdout.splitlines()[0].split()[-1][1:-2]
                                  ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^
IndexError: list index out of range
```
there may be an issue with Silicon. In this case, consider pulling Silicon's
source again, followed by building its jar.

Examples for the usage of plot.py can be found in
selected_plots/used_commands.md and profile-all.sh.
For the usage of profile.py, please take a look at its usage in
profile-all.sh. Finally, profile-all.sh contains comments describing its usage.

## `selected_plots/`
Contains plots comparing the results from different experiments.

## `experiments/`
### `program_proofs_example_10_2/`
We use the proof for `InsertCorrect` from [chapter 10.2 of Program Proofs encoded in Gobra](https://github.com/viperproject/program-proofs-gobra/blob/main/chapter10/examples_10.2.gobra)
to investigate the effect of "assisting" the verifier on execution time
and quantifier instantiations by means of intermediate assertions.

### `standard_library/`
We use parts of the standard library to investigate the effect of
making lemmas `opaque` on execution time and quantifier
instantiations.

### `synthetic_set/`
We create a synthetic example using sets that exhibits a relatively
high number of quantifier instantiations to investigate the effect of
- disabling set axiomatization and using the standard library to
manually prove all proof obligations
- "assisting" the verifier by calling lemmas from the standard library
that may be useful to prove the proof obligations

on execution time and quantifier instantiations.

Note that `fully_assisted/` is used for both types of experiments; the
difference is that in one case we disable set axiomatization by
passing the corresponding flag, while in the other case we do not.