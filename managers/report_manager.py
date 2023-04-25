import logging
from collections import Counter
from threading import Thread
from dotenv import dotenv_values
from http_handler.response_handler import ResponseHandler
from constants.error_message import ErrorMessage
from http_handler.request_handler import RequestHandler
from constants.status_code import StatusCode
from managers.time_converter import UTCTime
from dao.traderdao import TraderDao
from constants.info_message import InfoMessage


class Report:
    def __init__(self, trader_id: str):
        self.final_response = []
        self.pnl_new = []
        self.pnl = []
        self.pnl_per_day = None
        self.t_weekly_pnl = None
        self.dday = {}
        self.i = 0
        self.daily_closed_pnl_list = None
        self.active_order_exchange = None
        self.order_id_in_exchange = None
        self.total_pnl = None
        self.closed_pnl_list = None
        self.order_pnl = None
        self.seven_day_pnl_report = None
        self.request_handler = RequestHandler()
        self.config = dotenv_values(".env")
        self.trader_id = trader_id
        self.logger = logging.getLogger(__name__)
        self.exchange = "Bybit"
        self.utctime = UTCTime()
        self.win_rate = None
        self.wallet_ballance = None
        self.equity = None
        self.dao = TraderDao(self.config["DB_COLLECTION_NAME"])
        self.secret_key = None
        self.api_key = None
        self.thread_response = []

    # TODO: daily_total_asset, asset_per_coin, total_assets

    def asset_report(self):
        res = ResponseHandler()
        if self.secret_key is None:
            self.trader, status = self.trader_info(self.trader_id)
            if status == StatusCode.NOT_FOUND:
                res.set_status_code(status)
                res.set_response(self.trader)
                return res
        self.secret_key = self.trader['secret_key']
        self.api_key = self.trader['api_key']

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
            print(wallet_response)
            self.equity = wallet_response[0]["result"]["USDT"]["equity"]
            self.wallet_ballance = wallet_response[0]["result"]["USDT"]["wallet_balance"]
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
                for data in position_response[0]["result"]:
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

    # TODO: weekly_report_pnl, total_weekly_report_pnl
    def generate_weekly_pnl_report(self):

        res = ResponseHandler()
        coin, st = self.request_handler.send_get_request(
            base_url=self.config["COIN_BASE"],
            port=self.config["COIN_PORT"],
            end_point=self.config["COIN_URL"],
            timeout=self.config["EXCHANGE_TIMEOUT"],
            error_log_dict=ErrorMessage.EXCHANGE_ERROR_LOGS)
        if self.secret_key is None:
            self.trader, status = self.trader_info(self.trader_id)
            if status == StatusCode.NOT_FOUND:
                res.set_status_code(status)
                res.set_response(self.trader)
                return res
        self.secret_key = self.trader['secret_key']
        self.api_key = self.trader['api_key']
        self.id = self.trader['id']
        self.asset_report()
        cumulative_roi = []
        cumulative_pnl = []
        self.seven_day_pnl_report = []
        daily_roi = {}

        coins = [info["coin_symbol"] for info in coin]
        coins = list(dict.fromkeys(coins))
        self.closed_pnl_list = []
        self.order_id_in_exchange = []
        self.daily_closed_pnl_list = {}
        threads = []
        req_per_day = []

        for day in range(0, 7):
            self.dday.update({day: []})
            endtime = self.utctime.time_delta_timestamp(days=day)
            starttime = self.utctime.time_delta_timestamp(days=day + 1)
            self.logger.info("day {}".format(day))
            self.total_pnl = 0
            self.order_pnl = []
            for coin in coins:
                self.logger.info("prepare for new request to exchange")
                request_json = self.request_handler.create_json_from_args(key=self.api_key, secret=self.secret_key,
                                                                          exchange=self.exchange,
                                                                          start_time=str(int(starttime)),
                                                                          end_time=str(int(endtime)), symbol=coin,
                                                                          day=day)

                req_per_day.append(request_json)

        for req in req_per_day:
            thread = Thread(target=self.send_req, args=(req,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        self.t_weekly_pnl = 0
        self.pnl_per_day = {}
        for key, value in self.dday.items():
            d_pnl_list = []

            if self.dday[key]:
                t_day_pnl = 0
                for p in self.dday[key]:
                    t_day_pnl += p["closed_pnl"]
                    self.t_weekly_pnl += p["closed_pnl"]
                    self.closed_pnl_list.append(p)
                    d_pnl_list.append(p)
                roi = self.daily_roi_cumulative(d_pnl_list)
                daily_roi.update({f"{key} days ago": roi})
                cumulative_roi.insert(0, roi)
                cumulative_pnl.insert(0, t_day_pnl)

                self.pnl_per_day.update({"{} days ago".format(key): t_day_pnl})
            else:
                self.pnl_per_day.update({"{} days ago".format(key): 0})
                daily_roi.update({f"{key} days ago": 0})
                roi = self.daily_roi_cumulative(d_pnl_list)
                daily_roi.update({f"{key} days ago": roi})
                cumulative_roi.insert(0, roi)
                cumulative_pnl.insert(0, 0)

        roi_cumulative_chart = self.cumulative(cumulative_roi)
        pnl_cumulative_chart = self.cumulative(cumulative_pnl)
        res.set_status_code(StatusCode.SUCCESS)
        res.set_response(
            {
                "weekly_report_pnl": self.pnl_per_day, "total_weekly_report_pnl": self.t_weekly_pnl,
                "daily_roi": daily_roi,
                "cumulative_roi": roi_cumulative_chart, "cumulative_pnl": pnl_cumulative_chart})

        return res

    def send_req(self, req):

        pnl_response, response_status_code = self.request_handler.send_post_request(
            base_url=self.config["EXCHANGE_BASE_URL"],
            port=self.config["EXCHANGE_PORT"],
            end_point=self.config["EXCHANGE_POST_PNL_URL"],
            timeout=self.config["EXCHANGE_TIMEOUT"],
            error_log_dict=ErrorMessage.EXCHANGE_ERROR_LOGS,
            body=req)
        if response_status_code == StatusCode.SUCCESS and pnl_response[0]["ret_code"] == 0:
            if pnl_response[0]["result"]['data'] is not None:
                for closed in pnl_response[0]["result"]['data']:
                    self.dday[req["day"]].append(closed)
                    self.pnl.append(closed)

        pass

    @staticmethod
    def cumulative(sorted_ls: list):
        cu_list = []
        length = len(sorted_ls)
        cu_list = [sum(sorted_ls[0:x:1]) for x in range(0, length + 1)]
        res = cu_list[1:]
        res.reverse()

        return res

    def daily_roi_cumulative(self, daily_pnl_list):

        order_sell = []
        order_buy = []

        for order in daily_pnl_list:
            if order["side"] == "Sell":
                order_sell.append(order)
            if order["side"] == "Buy":
                order_buy.append(order)
        roi = self.roi_calculator(order_buy, order_sell)
        trader_total_roi = sum(roi)

        return trader_total_roi

    # TODO: "total_trades", "win_trade", "lose_trade","pnl_ratio","average_pnl", "trader_total_roi","trading_days"
    def seven_day_pnl_ratio_roi(self):
        res = ResponseHandler()

        if self.secret_key is None:
            self.trader, status = self.trader_info(self.trader_id)
            if status == StatusCode.NOT_FOUND:
                res.set_status_code(status)
                res.set_response(self.trader)
                return res
        self.secret_key = self.trader['secret_key']
        self.api_key = self.trader['api_key']
        self.id = self.trader['id']

        trading_days = self.utctime.days_between(self.trader["created_at"])

        useless_response = self.generate_weekly_pnl_report()
        if len(self.closed_pnl_list) > 0:
            negative = float(-1)
            total_profit = float(0)
            total_loss = float(0)
            total_trades = len(self.closed_pnl_list)
            win_trade = int(0)
            lose_trade = int(0)

            for pnl in self.closed_pnl_list:
                if pnl["closed_pnl"] > 0:
                    total_profit += pnl["closed_pnl"]
                    win_trade += 1
                elif pnl["closed_pnl"] < 0:
                    total_loss += pnl["closed_pnl"]
                    lose_trade += 1
            if total_loss == 0:
                pnl_ratio = 100

                if total_profit == 0:
                    pnl_ratio = 0

            else:

                pnl_ratio = total_profit / negative * total_loss
            if total_trades == 0:

                self.win_rate = 0
            else:
                self.win_rate = (win_trade / total_trades) * 100

            average_pnl = (total_loss + total_profit) / total_trades

            # Trader ROI
            # classify buy and sell positions
            order_buy = []
            order_sell = []
            for order in self.closed_pnl_list:
                if order["side"] == "Sell":
                    order_sell.append(order)
                if order["side"] == "Buy":
                    order_buy.append(order)
            # calculate roi
            useless = self.asset_report()

            roi_per_order = self.roi_calculator(order_buy, order_sell)

            trader_total_roi = sum(roi_per_order)

            res.set_status_code(StatusCode.SUCCESS)
            res.set_response({"total_trades": total_trades, "win_trade": win_trade, "lose_trade": lose_trade,
                              "win_rate": self.win_rate,
                              "pnl_ratio": pnl_ratio, "average_pnl": average_pnl, "trader_total_roi": trader_total_roi,
                              "trading_days": trading_days})
            return res


        else:
            res.set_status_code(StatusCode.SUCCESS)
            res.set_response({"total_trades": 0, "win_trade": 0, "lose_trade": 0,
                              "pnl_ratio": 0, "average_pnl": 0, "trader_total_roi": 0,
                              "trading_days": trading_days})
        return res

    def roi_calculator(self, order_buy, order_sell):
        roi_per_order = []
        for order in order_buy:
            if order["closed_pnl"] > 0:
                roi = float((order["closed_pnl"] / order["avg_entry_price"]) * (order["qty"] / self.equity))
                roi_per_order.append(roi)

            if order["closed_pnl"] < 0:
                roi = float(
                    (order["closed_pnl"] / order["avg_exit_price"]) * (order["qty"] / self.equity))
                roi_per_order.append(roi)

        for order in order_sell:
            if order["closed_pnl"] > 0:
                roi = float((order["avg_entry_price"] / order["closed_pnl"]) * (order["qty"] / self.equity))
                roi_per_order.append(roi)

            if order["closed_pnl"] < 0:
                roi = float(
                    (order["closed_pnl"] / order["avg_exit_price"]) * (order["qty"] / self.equity))
                roi_per_order.append(roi)

        return roi_per_order

    # TODO: get_history_from_mongo

    def get_history_from_mongo(self, condition: dict):
        try:
            result = self.dao.find(condition)
            self.logger.info(InfoMessage.DB_FIND)
        except Exception as error:
            self.logger.error(ErrorMessage.DB_SELECT)
            self.logger.error(error)
            raise Exception

        return result

    def active_order(self):
        res = ResponseHandler()

        if self.secret_key is None:
            self.trader, status = self.trader_info(self.trader_id)
            if status == StatusCode.NOT_FOUND:
                res.set_status_code(status)
                res.set_response(self.trader)
                return res
        self.secret_key = self.trader['secret_key']
        self.api_key = self.trader['api_key']
        self.id = self.trader['id']
        db_query = {"trader_info": self.id, "action": "open_position"}
        self.logger.info('trader id is {}'.format(self.id))
        orders_in_mongo = self.get_history_from_mongo(db_query)
        coins = [info["data"]["symbol"] for info in orders_in_mongo]
        coins = list(dict.fromkeys(coins))
        endtime = self.utctime.time_delta_timestamp(days=0)
        starttime = self.utctime.time_delta_timestamp(days=7)
        self.active_order_exchange = []
        order_id_in_mongo_db = []
        final_response = []
        for order in orders_in_mongo:
            try:
                order_id_in_mongo_db.append(order["result"][0]["result"]["order_id"])
            except (TypeError, KeyError):
                continue

        for coin in coins:
            self.logger.info("prepare for new request to exchange")
            for page in range(5):
                request_json = self.request_handler.create_json_from_args(key=self.api_key, secret=self.secret_key,
                                                                          order_status="Filled",
                                                                          exchange=self.exchange,
                                                                          limit="50",
                                                                          page=str(page),
                                                                          start_time=str(int(starttime)),
                                                                          end_time=str(int(endtime)), symbol=coin)
                self.logger.info("symbol {}".format(coin))
                self.logger.info("request json {}".format(request_json))
                active_order, response_status_code = self.request_handler.send_post_request(
                    base_url=self.config["EXCHANGE_BASE_URL"],
                    port=self.config["EXCHANGE_PORT"],
                    end_point=self.config["EXCHANGE_GET_ORDER"],
                    timeout=self.config["EXCHANGE_TIMEOUT"],
                    error_log_dict=ErrorMessage.EXCHANGE_ERROR_LOGS,
                    body=request_json)
                if response_status_code == StatusCode.SUCCESS and active_order[0]["ret_code"] == 0:
                    if active_order[0]["result"]['data'] is not None:
                        for order in active_order[0]["result"]['data']:
                            # if order["order_id"] in order_id_in_mongo_db:
                            if order["order_status"] in ["Filled"]:
                                final_response.append(order)
                            self.active_order_exchange.append(order["order_id"])
        number_of_trades = {}
        for coin in coins:
            per_coin = (1 for k in final_response if k.get("symbol") == coin)
            number_of_trades[coin] = sum(per_coin)
        res.set_response(number_of_trades)
        res.set_status_code(StatusCode.SUCCESS)
        return res

    def pnl_report(self):
        res = ResponseHandler()

        coin, st = self.request_handler.send_get_request(
            base_url=self.config["COIN_BASE"],
            port=self.config["COIN_PORT"],
            end_point=self.config["COIN_URL"],
            timeout=self.config["EXCHANGE_TIMEOUT"],
            error_log_dict=ErrorMessage.EXCHANGE_ERROR_LOGS)
        if self.secret_key is None:
            self.trader, status = self.trader_info(self.trader_id)
            if status == StatusCode.NOT_FOUND:
                res.set_status_code(status)
                res.set_response(self.trader)
                return res
        self.secret_key = self.trader['secret_key']
        self.api_key = self.trader['api_key']
        self.id = self.trader['id']
        self.asset_report()
        coins = [info["coin_symbol"] for info in coin]
        coins = list(dict.fromkeys(coins))
        threads = []
        req_per_day = []
        for day in range(0, 7):
            self.dday.update({day: []})
            endtime = self.utctime.time_delta_timestamp(days=day)
            starttime = self.utctime.time_delta_timestamp(days=day + 1)
            self.logger.info("day {}".format(day))
            self.total_pnl = 0
            self.order_pnl = []
            for coin in coins:
                self.logger.info("prepare for new request to exchange")
                request_json = self.request_handler.create_json_from_args(key=self.api_key, secret=self.secret_key,
                                                                          exchange=self.exchange,
                                                                          start_time=str(int(starttime)),
                                                                          end_time=str(int(endtime)), symbol=coin,
                                                                          day=day)

                req_per_day.append(request_json)

        for req in req_per_day:
            thread = Thread(target=self.send_req, args=(req,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        res.set_status_code(StatusCode.SUCCESS)
        res.set_response(
            self.pnl)

        return res

    def position(self):
        res = ResponseHandler()
        p_list = []

        if self.secret_key is None:
            self.trader, status = self.trader_info(self.trader_id)
            if status == StatusCode.NOT_FOUND:
                res.set_status_code(status)
                res.set_response(self.trader)
                return res
        self.secret_key = self.trader['secret_key']
        self.api_key = self.trader['api_key']
        request_json = self.request_handler.create_json_from_args(key=self.api_key, secret=self.secret_key,
                                                                  exchange=self.exchange)
        position_list, response_status_code = self.request_handler.send_post_request(
            base_url=self.config["EXCHANGE_BASE_URL"],
            port=self.config["EXCHANGE_PORT"],
            end_point=self.config["EXCHANGE_POST_POSITION_LIST_URL"],
            timeout=self.config["EXCHANGE_TIMEOUT"],
            error_log_dict=ErrorMessage.EXCHANGE_ERROR_LOGS,
            body=request_json)

        if response_status_code == StatusCode.SUCCESS and position_list[0]["ret_code"] == 0:
            if position_list[0]["result"] is not None:
                for position in position_list[0]["result"]:
                    if position["data"]["size"] != 0:
                        p_list.append(position["data"])

        res.set_response(p_list)
        res.set_status_code(StatusCode.SUCCESS)
        return res

    def active_order_new(self):
        res = ResponseHandler()

        if self.secret_key is None:
            self.trader, status = self.trader_info(self.trader_id)
            if status == StatusCode.NOT_FOUND:
                res.set_status_code(status)
                res.set_response(self.trader)
                return res
        self.secret_key = self.trader['secret_key']
        self.api_key = self.trader['api_key']
        self.id = self.trader['id']
        db_query = {"trader_info": self.id, "action": "open_position"}
        self.logger.info('trader id is {}'.format(self.id))
        orders_in_mongo = self.get_history_from_mongo(db_query)
        coins = [info["data"]["symbol"] for info in orders_in_mongo]
        coins = list(dict.fromkeys(coins))
        endtime = self.utctime.time_delta_timestamp(days=0)
        starttime = self.utctime.time_delta_timestamp(days=7)
        self.active_order_exchange = []
        order_id_in_mongo_db = []
        final_resonse = []
        for order in orders_in_mongo:
            try:
                order_id_in_mongo_db.append(order["result"][0]["result"]["order_id"])
            except (TypeError, KeyError):
                continue

        for coin in coins:
            self.logger.info("prepare for new request to exchange")
            request_json = self.request_handler.create_json_from_args(key=self.api_key, secret=self.secret_key,
                                                                      order_status="New",

                                                                      exchange=self.exchange,
                                                                      start_time=str(int(starttime)),
                                                                      end_time=str(int(endtime)), symbol=coin)
            self.logger.info("symbol {}".format(coin))
            self.logger.info("request json {}".format(request_json))
            active_order, response_status_code = self.request_handler.send_post_request(
                base_url=self.config["EXCHANGE_BASE_URL"],
                port=self.config["EXCHANGE_PORT"],
                end_point=self.config["EXCHANGE_GET_ORDER"],
                timeout=self.config["EXCHANGE_TIMEOUT"],
                error_log_dict=ErrorMessage.EXCHANGE_ERROR_LOGS,
                body=request_json)
            if response_status_code == StatusCode.SUCCESS and active_order[0]["ret_code"] == 0:
                if active_order[0]["result"]['data'] is not None:
                    for order in active_order[0]["result"]['data']:
                        # if order["order_id"] in order_id_in_mongo_db:
                        if order["order_status"] in ["New"]:
                            final_resonse.append(order)
                        self.active_order_exchange.append(order["order_id"])

        self.common_member(self.active_order_exchange, order_id_in_mongo_db)
        res.set_response(final_resonse)
        res.set_status_code(StatusCode.SUCCESS)
        return res

    # TODO: trader_info

    def trader_info(self, trader_user_id: str):
        req = RequestHandler()
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
        return response, response_status_code

    # TODO: INSTEAD OF TWO FOR LOOP, SEND QUERY REQUEST TO MONGO
    @staticmethod
    def common_member(a, b):
        a_set = set(a)
        b_set = set(b)

        if (a_set & b_set):
            print("Common id {}".format(a_set & b_set))
        else:
            print("No common elements")

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



