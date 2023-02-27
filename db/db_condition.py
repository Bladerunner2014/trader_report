from constants import sql_operator
from models.sample_model import SampleModel


class DBCondition:

    def __init__(self, term: str = None, operator: sql_operator.SqlOperator = None, const: str = None):
        self.term = term
        self.operator = operator
        self.const = const
        self.condition = ""

    def build_condition(self):
        self.condition = self.term + str(self.operator) + "'%s'" % self.const

    def __or__(self, other):
        or_condition = DBCondition()
        or_condition.condition = "(" + self.condition + " OR " + other.condition + ")"
        return or_condition

    def __and__(self, other):
        and_condition = DBCondition()
        and_condition.condition = "(" + self.condition + " AND " + other.condition + ")"
        return and_condition


if __name__ == '__main__':
    a = DBCondition(SampleModel.user_id, sql_operator.SqlOperator.EQL, "12")
    a.build_condition()
    b = DBCondition(SampleModel.user_id, sql_operator.SqlOperator.EQL, "15")
    b.build_condition()
    d = DBCondition(SampleModel.user_id, sql_operator.SqlOperator.GTE, "17")
    d.build_condition()
    c = a & ((b | d) & (b | a))
    print(c.condition)
