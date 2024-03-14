import asyncio
from obstacles import Obstacle, show_obstacles
import curses
import random
import time
from itertools import cycle
import os

from physics import update_speed
from curses_tools import draw_frame, get_frame_size
from explosion import explode
from game_scenario import get_garbage_delay_tics

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258
year = 1957

CORUTINES = []
OBSTACLES = []
OBSTACLES_IN_LAST_COLLISIONS = []

def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def fire(
    canvas,
    start_row,
    start_column,
    rows_speed=-0.2,
    columns_speed=0,
):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), "*")
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), "O")
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), " ")
    row += rows_speed
    column += columns_speed

    symbol = "-" if columns_speed else "|"

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), " ")
        row += rows_speed
        column += columns_speed
        for obstacle in OBSTACLES:

            result = obstacle.has_collision(row, column)
            if not result:
                continue
            else:
                OBSTACLES_IN_LAST_COLLISIONS.append(obstacle)
                return


async def show_gameover(canvas, row, column, item):
    draw_frame(canvas, row, column, item, negative=True)
    with open(
        "gameover.txt",
    ) as f:
        frame1 = f.read()
    while True:
        draw_frame(canvas, 20, 50, frame1)
        await sleep(1)


async def animate_spaceship(canvas, row, column, cadr, cadr2):

    frame1 = f"""{cadr}"""

    frame2 = f"""{cadr2}"""

    row_speed = column_speed = 0

    max_height, max_width = canvas.getmaxyx()  # max_shirina max_y visota

    rocket_height, rocket_width = get_frame_size(frame2)

    row += rocket_height
    column += rocket_width

    window_height = (max_height - 9) - 1
    window_width = (max_width - 5) - 1

    for item in cycle([frame1, frame1, frame2, frame2]):

        rows_direction, columns_direction, space_pressed = read_controls(canvas)

        row_speed, column_speed = update_speed(
            row_speed,
            column_speed,
            rows_direction,
            columns_direction,
        )

        row = min(row + rows_direction + row_speed, window_height)
        column = min(column + columns_direction + column_speed, window_width)

        for obstacle in OBSTACLES:
            result = obstacle.has_collision(row, column)
            if not result:
                continue
            else:
                await show_gameover(canvas, row, column, item)

        if space_pressed:
            if year > 2020:
                shot = fire(
                    canvas,
                    row,
                    column,
                    rows_speed=-0.99,
                )
                CORUTINES.append(shot)

        if row < 1:
            row = 1
        if row > window_height:
            row = row

        if column < 1:
            column = 1
        if column > window_width:
            column = column

        draw_frame(canvas, row, column, item)

        await sleep(1)
        draw_frame(canvas, row, column, item, negative=True)


async def blink(canvas, row, column, symbol, offset_tics):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)

        await sleep(offset_tics)
        canvas.addstr(row, column, symbol)

        await sleep(offset_tics)

        canvas.addstr(row, column, symbol, curses.A_BOLD)

        await sleep(offset_tics)

        canvas.addstr(row, column, symbol)

        await sleep(offset_tics)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)

    column = min(column, columns_number - 1)

    row = 0
    garbage_rows, garbage_colums = get_frame_size(garbage_frame)
    obstacle = Obstacle(row, column, garbage_rows, garbage_colums)
    OBSTACLES.append(obstacle)
    while row < rows_number:
        if obstacle in OBSTACLES_IN_LAST_COLLISIONS:
            await explode(canvas, obstacle.row, obstacle.column)
            return
        else:
            obstacle.row = row
            obstacle.column = column
            draw_frame(canvas, row, column, garbage_frame)
            await asyncio.sleep(0)
            draw_frame(canvas, row, column, garbage_frame, negative=True)
            row += speed


async def fill_orbit_with_garbage(canvas, max_x):
    garbage_path = "./garbage/"
    garbages = os.listdir(garbage_path)
    while True:
        amount_garbage = get_garbage_delay_tics(year)
        if amount_garbage:
            for amount in range(0, amount_garbage):
                garbage = random.choice(garbages)
                with open(f"{garbage_path}{garbage}", "r") as garbage_file:
                    frame = garbage_file.read()
                random_column = random.randint(0, max_x)
                coroutine = fly_garbage(
                    canvas, column=random_column, garbage_frame=frame
                )
                CORUTINES.append(coroutine)

                await sleep(random.randint(5, 10))

        await sleep(1)


async def year_tik(canvas):
    max_y, max_x = canvas.getmaxyx()
    while True:

        t = canvas.derwin(0, 0, max_y - 2, max_x - 100)
        global year
        t.addstr(1, 1, f"Year:{year}")
        year += 1
        canvas.refresh()
        await sleep(2)


def draw(canvas):
    canvas.border()
    curses.curs_set(False)
    canvas.nodelay(True)
    curses.curs_set(False)
    max_y, max_x = canvas.getmaxyx()

    with open(
        "rocket_frame_1.txt",
    ) as f:
        frame1 = f.read()

    with open(
        "rocket_frame_2.txt",
    ) as f:
        frame2 = f.read()

    height = []
    width = []
    symbols = ["+", "*", ".", ":"]

    for number in range(100):
        y = random.randint(0, max_y)
        if y >= max_y:
            continue

        x = random.randint(max_y, max_x)
        if x >= max_x:
            continue
        height.append(y)
        width.append(x)

    for _ in range(100):
        offset_tics = random.randint(1, 5)
        star = blink(
            canvas,
            random.choice(height),
            random.choice(width),
            random.choice(symbols),
            offset_tics,
        )
        CORUTINES.append(star)

    corable = animate_spaceship(canvas, 18, 77, frame1, frame2)

    add_garbage = fill_orbit_with_garbage(canvas, max_x)

    show_year = year_tik(canvas)
    CORUTINES.append(add_garbage)
    CORUTINES.append(show_year)
    CORUTINES.append(corable)

    while True:
        for corutine in CORUTINES.copy():
            try:
                corutine.send(None)

            except StopIteration:
                CORUTINES.remove(corutine)

        if len(CORUTINES) == 0:
            break
        canvas.refresh()
        time.sleep(1)


if __name__ == "__main__":
    curses.update_lines_cols()

    curses.wrapper(draw)
