def draw_frame(canvas, start_row, start_column, text, negative=False):
  """Draw multiline text fragment on canvas, erase text instead of drawing if negative=True is specified."""

  rows_number, columns_number = canvas.getmaxyx()

  for row, line in enumerate(text.splitlines(), round(start_row)):
    if row < 0:
      continue

    if row >= rows_number:
      break

    for column, symbol in enumerate(line, round(start_column)):
      if column < 0:
        continue

      if column >= columns_number:
        break

      if symbol == ' ':
        continue

      if row == rows_number - 1 and column == columns_number - 1:
        continue

      symbol = symbol if not negative else ' '
      canvas.addch(row, column, symbol)
