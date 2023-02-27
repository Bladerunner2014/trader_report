import logging
from collections import Counter

from dotenv import dotenv_values
from http_handler.response_handler import ResponseHandler
from constants.error_message import ErrorMessage
from http_handler.request_handler import RequestHandler
from constants.status_code import StatusCode
from time_converter import UTCTime
from dao.traderdao import TraderDao
from constants.info_message import InfoMessage


class Report:
    def __init__(self, trader_id):
        self.order_pnl = None
        self.seven_day_pnl_report = None
        self.request_handler = RequestHandler()
        self.config = dotenv_values(".env")
        self.trader_id = trader_id
        self.logger = logging.getLogger(__name__)
        self.trader, status = self.trader_info(trader_id)
        self.secret_key = self.trader['secret_key']
        self.api_key = self.trader['api_key']
        self.exchange = self.trader["exchange"]
        self.utctime = UTCTime()
        self.win_rate = None
        self.wallet_ballance = None
        self.equity = None
        self.dao = TraderDao(self.config["DB_COLLECTION_NAME"])

    # TODO: daily_total_asset, asset_per_coin, total_assets

    def asset_report(self):
        res = ResponseHandler()

        request_json = self.request_handler.create_json_from_args(key=self.api_key, secret=self.secret_key,
                                                                  exchange=self.exchange)
        wallet_response, wallet_response_status_code = self.request_handler.send_post_request(
            base_url=self.config["EXCHANGE_BASE_URL"],
            port=self.config["EXCHANGE_PORT"],
            end_point=self.config["EXCHANGE_POST_BALANCE_URL"],
            timeout=self.config["EXCHANGE_TIMEOUT"],
            error_log_dict=ErrorMessage.EXCHANGE_ERROR_LOGS,
            body=request_json)
        if wallet_response_status_code == StatusCode.SUCCESS:
            self.equity = wallet_response["USDT"]["equity"]
            self.wallet_ballance = wallet_response["USDT"]["wallet_balance"]
            position_response, position_response_status_code = self.request_handler.send_post_request(
                base_url=self.config["EXCHANGE_BASE_URL"],
                port=self.config["EXCHANGE_PORT"],
                end_point=self.config["EXCHANGE_POST_POSITION_LIST_URL"],
                timeout=self.config["EXCHANGE_TIMEOUT"],
                error_log_dict=ErrorMessage.EXCHANGE_ERROR_LOGS,
                body=request_json)
            if position_response_status_code == StatusCode.SUCCESS:
                asset_buy = {}
                asset_sell = {}
                for data in position_response:
                    if data["data"]["size"] != 0:
                        if data["data"]["side"] == "Buy":
                            asset_buy.update({data["data"]["symbol"]: float(data["data"]["position_value"])})
                        if data["data"]["side"] == "Sell":
                            asset_sell.update({data["data"]["symbol"]: float(data["data"]["position_value"])})
                asset = dict(Counter(asset_buy) + Counter(asset_sell))
                total_asset = sum(asset.values())
                print(total_asset)
                res.set_status_code(StatusCode.SUCCESS)
                res.set_response({"total_asset": self.equity, "asset_per_coin": asset})
                return res
            else:
                res.set_status_code(StatusCode.INTERNAL_ERROR)
                res.set_response({"message": ErrorMessage.EXCHANGE_ERROR_LOGS, "response": wallet_response})
                return res
        else:
            res.set_status_code(StatusCode.INTERNAL_ERROR)
            res.set_response({"message": ErrorMessage.EXCHANGE_ERROR_LOGS, "response": wallet_response})
            return res

    # TODO: total_daily_pnl
    def generate_daily_pnl_report(self, user_id):
        endtime = self.utctime.time_delta_timestamp()
        starttime = self.utctime.time_delta_timestamp(days=1)
        res = ResponseHandler()
        db_query = {"trader_id": user_id, "action": "orders_list"}
        orders_in_mongo = self.get_history_from_mongo(db_query)
        coins = [info["symbol"] for info in orders_in_mongo]
        order_pnl = []
        for coin in coins:
            request_json = self.request_handler.create_json_from_args(key=self.api_key, secret=self.secret_key,
                                                                      exchange=self.exchange,
                                                                      startTime=starttime, endTime=endtime, symbol=coin)
            pnl_response, pnl_response_status_code = self.request_handler.send_post_request(
                base_url=self.config["EXCHANGE_BASE_URL"],
                port=self.config["EXCHANGE_PORT"],
                end_point=self.config["EXCHANGE_POST_PNL_URL"],
                timeout=self.config["EXCHANGE_TIMEOUT"],
                error_log_dict=ErrorMessage.EXCHANGE_ERROR_LOGS,
                body=request_json)
            if pnl_response_status_code == StatusCode.SUCCESS:

                pnl_response = pnl_response["result"]
                matched_pnl = self.filter_orders(exchange_orders=pnl_response["data"], db_orders=orders_in_mongo)

                for orders in matched_pnl:
                    order_pnl.append(float(orders["closed_pnl"]))

            else:
                res.set_status_code(StatusCode.INTERNAL_ERROR)
                res.set_response({"message": ErrorMessage.EXCHANGE_ERROR_LOGS, "response": pnl_response})
                return res
        total_daily_pnl = sum(order_pnl)
        res.set_status_code(StatusCode.SUCCESS)
        res.set_response({"total_daily_pnl": total_daily_pnl})
        return res

    # TODO: weekly_report_pnl, total_weekly_report_pnl
    def generate_weekly_pnl_report(self):
        res = ResponseHandler()
        self.seven_day_pnl_report = []
        weekly_pnl = {}
        for day in range(0, 7):
            endtime = self.utctime.time_delta_timestamp(days=day)
            starttime = self.utctime.time_delta_timestamp(days=day + 1)
            db_query = {"trader_id": self.trader_id, "action": "orders_list"}
            orders_in_mongo = self.get_history_from_mongo(db_query)
            coins = [info["symbol"] for info in orders_in_mongo]
            self.order_pnl = []
            for coin in coins:
                request_json = self.request_handler.create_json_from_args(key=self.api_key, secret=self.secret_key,
                                                                          exchange=self.exchange, start_time=starttime,
                                                                          end_time=endtime, symbol=coin)
                pnl_response, response_status_code = self.request_handler.send_post_request(
                    base_url=self.config["EXCHANGE_BASE_URL"],
                    port=self.config["EXCHANGE_PORT"],
                    end_point=self.config["EXCHANGE_POST_PNL_URL"],
                    timeout=self.config["EXCHANGE_TIMEOUT"],
                    error_log_dict=ErrorMessage.EXCHANGE_ERROR_LOGS,
                    body=request_json)
                if response_status_code == StatusCode.SUCCESS:

                    pnl_response = pnl_response["result"]

                    matched_pnl = self.filter_orders(exchange_orders=pnl_response["data"], db_orders=orders_in_mongo)
                    self.seven_day_pnl_report.append(matched_pnl)
                    for orders in matched_pnl:
                        self.order_pnl.append(float(orders["closed_pnl"]))
                else:
                    res.set_status_code(StatusCode.INTERNAL_ERROR)
                    res.set_response({"message": ErrorMessage.EXCHANGE_ERROR_LOGS, "response": pnl_response})
                    return res
            total_pnl = sum(self.order_pnl)
            weekly_pnl.update({f"{day} days ago": total_pnl})
        total_weekly_pnl = sum(weekly_pnl.values())

        res.set_status_code(StatusCode.SUCCESS)
        res.set_response({"weekly_report_pnl": weekly_pnl, "total_weekly_report_pnl": total_weekly_pnl})
        return res

    # TODO: "total_trades", "win_trade", "lose_trade","pnl_ratio","average_pnl", "trader_total_roi","trading_days"

    def seven_day_pnl_ratio_roi(self):
        res = ResponseHandler()

        useless_response = self.generate_weekly_pnl_report()

        if self.seven_day_pnl_report:
            pnl_for_ever = self.unpack_weekly_pnl(self.seven_day_pnl_report)
            total_profit = float(0)
            total_loss = float(0)
            total_trades = len(self.order_pnl)
            win_trade = int(0)
            lose_trade = int(0)

            for pnl in self.order_pnl:
                if pnl > 0:
                    total_profit += pnl
                    win_trade += 1
                elif pnl < 0:
                    total_loss += pnl
                    lose_trade += 1
            pnl_ratio = total_profit / total_loss
            average_pnl = win_trade / total_trades

            # Trader ROI
            # classify buy and sell positions
            order_buy = []
            order_sell = []
            for order in pnl_for_ever:
                if order["side"] == "Sell":
                    order_sell.append(order)
                if order["side"] == "Buy":
                    order_buy.append(order)
            # calculate roi
            total_asset, status = self.asset_report().generate_response()
            total_asset = total_asset["total_asset"]
            roi_per_order = []
            negative = float(-1)

            for order in order_buy:
                if order["pnl"] > 0:
                    roi = float((order["take_profit"] / order["price"]) * (order["qty"] / total_asset))
                    roi_per_order.append(roi)

                if order["pnl"] < 0:
                    roi = float(negative * (order["price"] / order["stop_loss"]) * (order["qty"] / total_asset))
                    roi_per_order.append(roi)

            for order in order_sell:
                if order["pnl"] > 0:
                    roi = float((order["price"] / order["take_profit"]) * (order["qty"] / total_asset))
                    roi_per_order.append(roi)

                if order["pnl"] < 0:
                    roi = float(negative * (order["stop_loss"] / order["price"]) * (order["qty"] / total_asset))
                    roi_per_order.append(roi)

            trader_total_roi = sum(roi_per_order)
            trading_days = self.utctime.days_between(self.trader["created_at"])

            res.set_status_code(StatusCode.SUCCESS)
            res.set_response({"total_trades": total_trades, "win_trade": win_trade, "lose_trade": lose_trade,
                              "pnl_ratio": pnl_ratio, "average_pnl": average_pnl, "trader_total_roi": trader_total_roi,
                              "trading_days": trading_days})
            return res

        else:
            res.set_status_code(StatusCode.INTERNAL_ERROR)
        return res

    # TODO: get_history_from_mongo

    def get_history_from_mongo(self, condition: dict):
        try:
            result = self.dao.find(condition)
            self.logger.error(InfoMessage.DB_FIND)
        except Exception as error:
            self.logger.error(ErrorMessage.DB_SELECT)
            self.logger.error(error)
            raise Exception

        list_of_orders = []
        for item in result:
            list_of_orders.append(item["data"])

        return list_of_orders

    # TODO: trader_info

    def trader_info(self, trader_user_id: str):
        req = RequestHandler()
        res = ResponseHandler()
        try:
            response, response_status_code = req.send_get_request(base_url=self.config["TRADER_BASE_URL"],
                                                                  end_point=self.config[
                                                                                "TRADER_GET_URL"] + trader_user_id,
                                                                  port=self.config["TRADER_PORT"],

                                                                  timeout=self.config["TRADER_TIMEOUT"],
                                                                  error_log_dict={"message": ErrorMessage.TRADER_ERROR})
        except Exception as error:
            self.logger.error(ErrorMessage.TRADER_ERROR)
            self.logger.error(error)
            raise Exception

        if response_status_code == StatusCode.SUCCESS:
            res.set_status_code(StatusCode.SUCCESS)
            res.set_response(response)
            return res.status_code, res.response
        else:
            res.set_status_code(StatusCode.BAD_REQUEST)
            res.set_response(response)
            return res.generate_response()

    # TODO: INSTEAD OF TWO FOR LOOP, SEND QUERY REQUEST TO MONGO
    @staticmethod
    def filter_orders(exchange_orders, db_orders):
        # match_ord = []
        # for ord in exchange_orders:
        #     condition = {"trader_info": ord["order_id"], "action": "open_position"}
        #     try:
        #         match_ord.append(self.dao.find(condition))
        #         self.logger.error(InfoMessage.DB_FIND)
        #     except Exception as error:
        #         self.logger.error(ErrorMessage.DB_SELECT)
        #         self.logger.error(error)
        #         raise Exception
        matched_orders = []
        for e_order in exchange_orders:
            for d_order in db_orders:
                if e_order["order_id"] == d_order["order_id"]:
                    d_order["pnl"] = e_order["closed_pnl"]
                    matched_orders.append(d_order)

        return matched_orders

    @staticmethod
    def create_dict_from_two_lists(res: list, keys: list):

        results_list = []
        for ls in res:
            results_list.append({keys[i]: ls[i] for i in range(len(keys))})
        if len(results_list) == 1:
            results_list = results_list[0]
        return results_list

    @staticmethod
    def unpack_weekly_pnl(ls: list):
        week_pnl = []
        for day in ls:
            for pnl in day:
                week_pnl.append(pnl)

        return week_pnl
