"""Pure domain layer for Activation Desk (Pipeline 1 and 2 rules).

Standard library only: no FastAPI, SQLAlchemy or database imports here.
Statuses, flags, scores and lanes are always computed from the account
facts; they are never stored. Every function that depends on the current
date takes ``today`` as an explicit parameter so results stay
deterministic and testable.
"""
