from brownie import (
    network,
    accounts,
    config,
)


LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local", "mainnet-fork"]


def get_account(index=None, id=None):
    # accounts.add(os.get_env())
    # accounts.load("id")
    if index:
        return account[index]
    if id:
        return accounts.load(id)
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        account = accounts[0]
        return account

    # account = accounts.add(os.getenv("private_key"))
    return accounts.add(config["wallets"]["from_key"])
