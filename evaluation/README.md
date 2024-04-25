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