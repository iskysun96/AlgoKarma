# from pyteal import Seq, App, Txn, Return, Int, Gtxn, TxnType, Bytes, If, And, Global, Cond, OnComplete, Addr,Assert, AssetHolding
from pyteal import *

def withdrawal_escrow(app_id, asa_id):
    Fee = Int(1000)

    asa_opt_in = And(
        Txn.type_enum() == TxnType.AssetTransfer,
        Txn.fee() <= Fee,
        Txn.xfer_asset() == Int(asa_id),
        Txn.asset_amount() == Int(0),
        Txn.rekey_to() == Global.zero_address(),
        Txn.asset_close_to() == Global.zero_address()
    )

    give_karma = And(
        Gtxn[0].application_id() == Int(app_id),
        Gtxn[0].type_enum() == TxnType.ApplicationCall,
        Gtxn[0].on_completion() == OnComplete.NoOp,
        Gtxn[0].application_args[0] == Bytes("CheckIn"),
        Gtxn[1].type_enum() == TxnType.AssetTransfer,
        Gtxn[1].xfer_asset() == Int(asa_id),
        Gtxn[1].fee() <= Fee,
        Txn.rekey_to() == Global.zero_address(),
        Txn.asset_close_to() == Global.zero_address()
    )
    
    clawback_karma = And(
        Gtxn[0].application_id() == Int(app_id),
        Gtxn[0].type_enum() == TxnType.ApplicationCall,
        Gtxn[0].on_completion() == OnComplete.NoOp,
        Gtxn[0].application_args[0] == Bytes("Punish"),
        Gtxn[1].type_enum() == TxnType.AssetTransfer,
        Gtxn[1].xfer_asset() == Int(asa_id),
        Gtxn[1].fee() <= Fee,
        Txn.rekey_to() == Global.zero_address(),
        Txn.asset_close_to() == Global.zero_address()
    )

    program = Cond(
        [Global.group_size() == Int(1), asa_opt_in],
        [And(
            Global.group_size() == Int(2),
            Gtxn[0].application_args[0] == Bytes("CheckIn")
        ), give_karma],
        [And(
            Global.group_size() == Int(2),
            Gtxn[0].application_args[0] == Bytes("Punish")
        ), clawback_karma],
    )

    return compileTeal(program, Mode.Signature, version=3)


# asa_id = 0

# app_id = 0

# if __name__ == "__main__":

#     with open('withdrawal_escrow.teal', 'w') as f:
#         compiled = withdrawal_escrow(app_id, asa_id)
#         f.write(compiled)