from aiogram.fsm.state import State, StatesGroup

class AddProductsStates(StatesGroup):
    waiting_for_products = State()

class SellProductStates(StatesGroup):
    selecting_category = State()
    selecting_product = State()
    entering_quantity = State()
    entering_price = State()