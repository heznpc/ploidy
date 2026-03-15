# Architecture

> This document will be expanded as the implementation progresses.

## Overview

Diploid is an MCP server that orchestrates structured debates between two sessions of the same model with intentionally asymmetric context.

## Components

- **server** -- MCP tool interface
- **protocol** -- Debate state machine
- **session** -- Context management and asymmetry
- **convergence** -- Synthesis and analysis engine
- **store** -- SQLite persistence layer

## Data Flow

```
Client (MCP) -> Server -> SessionManager -> DebateProtocol -> ConvergenceEngine
                                                 |
                                            DebateStore (SQLite)
```
