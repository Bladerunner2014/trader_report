from dao.traderdao import TraderDao

dao = TraderDao("position_db")
query = {"trader_info": 4, "action": "open_position"}

print(dao.find(query))
