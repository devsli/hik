Before clone
~~~~~~~~~~~~

To properly save/load SQLite3 database you first need to tune your git::

  cat <<'EOF'> ~/bin/sqlite3.clean
  #!/bin/sh
  DB=$(mktemp)
  cat - > $DB
  sqlite3 $DB .dump
  rm $DB
  EOF
  chmod +x ~/bin/sqlite3.clean
  
  cat <<'EOF'> ~/bin/sqlite3.smudge
  #!/bin/sh
  DB=$(mktemp)
  cat - | sqlite3 $DB
  cat $DB
  rm $DB
  EOF
  chmod +x ~/bin/sqlite3.smudge
  
  git config --global filter.sqlite.clean sqlite3.clean
  git config --global filter.sqlite.smudge sqlite3.smudge

Как использовать
~~~~~~~~~~~~~~~~

Поиск старых выпусков::

  python -m kih fetchold

Загрузка новых выпусков из RSS::

  python -m kih fetch

Получить ссылки на все выпуски::

  python -m kih urls
