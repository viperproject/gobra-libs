# gobra-libs
This project contains definitions and lemmas that are generally useful to any verification project using Gobra.
Currently, the project contains packages to reason about sets (`sets`), sequences (`seqs`), maps in Go (`gomaps`), and mathematical maps (`dicts`), but we hope to gradually increase its functionality.
We draw inspiration from multiple sources, including [dafny-lang/libraries](https://github.com/dafny-lang/libraries), [vstd](https://github.com/verus-lang/verus/tree/main/source/vstd), and the [Why3 standard library](https://www.why3.org/stdlib/). Furthermore, this library builds on top of utility packages originally developed for diverse verification projects, e.g., [VerifiedSCION](https://github.com/viperproject/VerifiedSCION) and [viperproject/program-proofs-gobra](https://github.com/viperproject/program-proofs-gobra)

This project was originally developed as a Practical Work project by Daniel Nezamabadi at ETH Zurich. You can find more details about it [in the report](https://ethz.ch/content/dam/ethz/special-interest/infk/chair-program-method/pm/documents/Education/Theses/Daniel_Nezamabadi_PW_Report.pdf).

## Contributing
The goal of this project is to make it easy to maintain and re-use common definitions across different verification projects that use Gobra. If you find yourself re-using definitions between projects, or if you develop libraries that might benefit others, please consider contributing.
