import random
import sys
import json
import math

import numpy as np
import yaml

from math import comb
from collections import defaultdict

from matplotlib import pyplot as pp


# open path to YAML config file
with open(sys.argv[1]) as fin:
    params = yaml.load(fin, Loader=yaml.CLoader)

all_numbers = list(range(params['min'], params['max'] + 1))
steps = {int(k): v for k, v in params['payout_step_sizes'].items()}
pcts = {int(k): v for k, v in params['payout_pot_percents'].items()}
step_up_ticket_count = params['step_up_ticket_count']
price = params['price']
min_pot = params['min_pot']
n_rounds = params['rounds']

# running total tax
tax = 0

# running lotto balance (the pot), updated with each round
balance = 0

# init various time series for graphing
y_balance = []
y_payout = []
y_tax = []
y_users = []

# map from winning match counts to lists of payouts,
# aggregated across all rounds of the sim, used for stats
payout_lists = defaultdict(list)

def draw():
    nums = set()
    while len(nums) < params['n']:
        nums.add(random.choice(all_numbers))
    return nums

# for each round...
for t in range(n_rounds):
    print(f'Round {t + 1}')
    tickets = []

    n_users = random.randint(
        params['min_users'], 
        min(params['max_users'], int(params['min_users'] + (params['max_users'] - params['min_users']) * (t / n_rounds)**1.2))
    )

    # simulate each user buying some tickets.
    # note that tickets are unique per user
    for i in range(n_users):
        n_user_tickets = random.randint(
            params['min_tickets_per_user'], 
            params['max_tickets_per_user']
        )

        ticket_group = {}

        while len(ticket_group) < n_user_tickets:
            ticket_numbers = draw()
            ticket_hash = ':'.join(str(x) for x in sorted(list(ticket_numbers)))
            ticket_group[ticket_hash] = ticket_numbers

        tickets.extend(ticket_group.values())

    n_tickets = len(tickets)
    balance += (n_tickets * price) * 0.9
    tax += (n_tickets * price) * 0.1

    computed_payouts = {
        k: max(price, v * (math.log2(n_tickets/step_up_ticket_count + 1) + 1)**1.5) 
        for k, v in steps.items()
    }

    visited_pcts = set()
    winning_numbers = draw()  # winning numbers for the round
    payout = 0  # running total payout for the round

    # now find winners and compute round's payout, adjust
    # taxes if need be, and update remaining balance
    for i, ticket_numbers in enumerate(tickets):
        ticket_payout = 0
        n = len(ticket_numbers & winning_numbers)

        if n in computed_payouts:
            payout += computed_payouts.get(n, 0)
            ticket_payout += computed_payouts.get(n, 0)

        if n in pcts and n not in visited_pcts:
            visited_pcts.add(n)
            pct = pcts[n]
            amount = pct * balance
            tax_amount = amount * 0.05
            post_taxed_amount = amount - tax_amount
            payout += post_taxed_amount
            ticket_payout += post_taxed_amount
            tax += tax_amount

        if ticket_payout:
            payout_lists[n].append(ticket_payout)

    # update session balance
    balance -= payout

    if balance < min_pot:
        delta = min_pot - balance
        balance += delta
        tax -= delta

    y_payout.append(payout)
    y_balance.append(balance)
    y_tax.append(tax)
    y_users.append(n_users)


# print out some stats
for n, payout_list in payout_lists.items():
    print(f'mean payout for {n}/{params["n"]} matches: {np.mean(payout_list)} GLTO')
    print(f'min payout for {n}/{params["n"]} matches: {np.min(payout_list)} GLTO')
    print(f'max payout for {n}/{params["n"]} matches: {np.max(payout_list)} GLTO')
    print()

# graph it
x = np.arange(len(y_balance))

pp.plot(x, y_balance, label="Pot Size")
pp.plot(x, y_payout, label="Total Payout")
pp.plot(x, y_tax, label="House Revenue")
#pp.plot(x, y_users, label="User Count")
pp.ylabel("GLTO")
pp.xlabel("Lotto Round")
pp.legend()
pp.show()
