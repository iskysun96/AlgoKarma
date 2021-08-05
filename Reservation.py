# from pyteal import Seq, App, Txn, Return, Int, Gtxn, TxnType, Bytes, If, And, Global, Cond, OnComplete, Addr,Assert, AssetHolding
from pyteal import *


def withdrawal_approval():
    on_creation = Seq([
        Assert(
            Txn.application_args.length() == Int(3),
            Txn.sender() == Addr(karma_platform_address_comes_here)
        ),
        App.globalPut(Bytes("KarmaID"), Txn.application_args[0]),
        App.globalPut(Bytes("KarmaLevel"), Txn.application_args[1]),
        App.globalPut(Bytes("RestaurantAddr"), Txn.application_args[2]),
        Return(Int(1))
    ])

    handle_optin = Return(Int(1))

    handle_closeout = Seq([ 
        App.localGet(Txn.sender(), Bytes("ReservationTime") + Int(600) < Global.latest_timestamp())
    ])

    handle_updateapp = Return(Int(0))

    handle_deleteapp = Return(Int(0))

    karmaHolding = AssetHolding.balance(Int(0), App.globalGet(Bytes("KarmaID")))

    addEscrow = Seq([ 
        Assert(
            And(
                Txn.sender() == Global.creator_address(),
                Txn.application_args.length() == Int(2)
            )
        ),
        App.globalPut(Bytes("KarmaPlatformEscrow"), Txn.application_args[1]),
    ])

    make_reservation = Seq([ 
        karmaHolding,
        And(
            Txn.application_args.length() == Int(2),
            karmaHolding.hasValue(),
            karmaHolding.value() >= App.globalGet("KarmaLevel"),
        ),
        App.localPut(Int(0), Bytes("ReservationTime"), Txn.application_args[1])
    ])

    check_in = Seq(
        Assert(
            And(
                Gtxn[0].sender() == App.globalGet(Bytes("RestaurantAddr")),
                App.localGet(Int(1), Bytes("ReservationTime")) >= Global.latest_timestamp(),
                Gtxn[1].receiver() == Gtxn[0].accounts[1]
            )
        ),
        App.localPut(Int(1), Bytes("ReservationTime"), Int(0)) #customer account = second account in accounts array
    )

    punish = Seq([ 
        Assert(
            And(
                Gtxn[0].sender() == App.globalGet(Bytes("RestaurantAddr")),
                App.localGet(Int(1), Bytes("ReservationTime")) > Int(0),
                App.localGet(Int(1), Bytes("ReservationTime")) + Int(600) < Global.latest_timestamp(), # 600 = 10 minutes in unix time. 10 minute grace period
                Gtxn[1].receiver() == App.globalGet(Bytes("KarmaPlatformEscrow"))
            )
        ),
        App.localPut(Int(1), Bytes("ReservationTime"), Int(0))
    ])

    handle_noop = Cond(
        [And(
            Global.group_size() == Int(1),
            Txn.application_args[0] == Bytes("AddEscrow")
        ), addEscrow],
        [And(
            Global.group_size() == Int(1),
            Txn.application_args[0] == Bytes("Reserve")
        ), make_reservation],
        [And(
            Global.group_size() == Int(2),
            Gtxn[0].application_args[0] == Bytes("CheckIn")
        ), check_in],
        [And(
            Global.group_size() == Int(2),
            Gtxn[0].application_args[0] == Bytes("Punish")
        ), punish]
    )

    
    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.OptIn, handle_optin],
        [Txn.on_completion() == OnComplete.CloseOut, handle_closeout],
        [Txn.on_completion() == OnComplete.UpdateApplication, handle_updateapp],
        [Txn.on_completion() == OnComplete.DeleteApplication, handle_deleteapp],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop]
    )

    return program


def clear_state_program():
    program = Return(Int(1))
    return program


# if __name__ == "__main__":
#     with open('withdrawal_approval.teal', 'w') as f:
#         compiled = withdrawal_approval()
#         f.write(compiled)