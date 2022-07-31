from brownie import accounts, config, network, interface
from scripts.helpful_scripts import get_account
from scripts.get_weth import get_weth
import time
from web3 import Web3

# 0.1
amount = Web3.toWei(0.1, "ether")


def get_lending_pool():
    # lending pool address may vary so we need an Address provider to get us the actual address
    # we need an abi and an address.
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    # To return lending pool contract, we need;
    # ABI - ?
    # address - check! of the actual lending pool.
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool


def approve_erc20(amount, spender, erc20_address, account):
    print("Approving ERC20 token spend...")
    # We would need the address and the ABI
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    time.sleep(1)
    print("Approved!")
    pass


def get_borrowable_data(lending_pool, account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"You have {total_collateral_eth} worth of ETH deposited.")
    print(f"You have {total_debt_eth} worth of ETH borrowed.")
    print(f"You can borrow {available_borrow_eth} worth of ETH.")
    print(f"Your debt health factor is {health_factor}.")
    return (float(available_borrow_eth), float(total_debt_eth))


def get_asset_price(price_feed_address):
    # ABI and an Address
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"The DAI/ETH price is {converted_latest_price}")
    return float(converted_latest_price)


def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][network.show_active()]["dai_token_address"],
        account,
    )
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token_address"],
        amount,
        1,
        account.address,
        {"from": account},
    )
    time.sleep(1)


def aave_borrow():
    account = get_account()
    weth_erc20_address = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() == "mainnet-fork":
        get_weth()
        time.sleep(1)
    # ABI and Address of lending pool contract
    lending_pool = get_lending_pool()
    # Approve sending our ERC 20 token
    approve_erc20(amount, lending_pool.address, weth_erc20_address, account)
    # To deposit into aave
    print("Depositing WETH...")
    tx = lending_pool.deposit(
        weth_erc20_address, amount, account.address, 0, {"from": account}
    )
    tx.wait(1)
    print("Deposited funds!")
    # how much can we actually borrow
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    # @dev to borrow some DAI!
    print("Borrowing Some Dai, Calling a pricefeed contract.")
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    # converting borrowable eth to borrowable dai * 95% (to not get liq)
    print(f"we're going to borrow {amount_dai_to_borrow} DAI ")
    # Borrow logic
    dai_token_address = config["networks"][network.show_active()]["dai_token_address"]
    borrow_tx = lending_pool.borrow(
        dai_token_address,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print("Successfully borrowed DAI")
    get_borrowable_data(lending_pool, account)
    repay_all(Web3.toWei(total_debt, "ether"), lending_pool, account)
    # repay_all(Web3.toWei(amount_dai_to_borrow, "ether"), lending_pool, account)
    print(
        "@dev has successfully deposited , borrowed and repayed a loan with Aave, Brownie and Chainlink! "
    )


def main():
    aave_borrow()
