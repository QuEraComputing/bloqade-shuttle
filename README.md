# Bloqade-Shuttle

Bloqade-shuttle is an SDK for simulation and running neutral atom quantum computers
with explicit shuttling. The goal of this project is to provide both a frontend language
for programming neutral atom quantum computers as well as an IR for optimizing
scheduling of atom shuttling operations. While this project falls under the 
[`Bloqade`](https://bloqade.quera.com/latest/) umbrella, we are still in the early
stages of development. We are focusing on building a steering committee for this
project and gathering feedback on the design of the language and the IR. Our ultimate
goal is to work together, furthering the development of neutral atom quantum computers
and their applications.

The IR and language are built with [`Kirin`](https://queracomputing.github.io/kirin/latest/).
Kirin not only provides composability via an MLIR-like IR but also provides a built-in,
customizable Python lowering, enabling the ability to embed the DSL in Python. Kirin
also has tools for static analysis along with a rewrite infrastructure in Python,
making it an ideal choice for scientific applications like Bloqade-Shuttle.

## Installation

```bash
uv add bloqade-shuttle
```
<!--- TODO: update links to point to documentation website once available. --->
See [Installation](https://improved-dollop-7j6z8v7.pages.github.io/dev/install) for more details.

Check out new [Blog](https://improved-dollop-7j6z8v7.pages.github.io/dev/blog/) to understand more about tools and shuttle.
