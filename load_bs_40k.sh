DIR="work_in_progress/battlescribe/fixtures/40k"
if [ ! -d "$DIR" ]; then
  git clone https://github.com/BSData/wh40k-10e.git $DIR
else
  T=$(pwd)
  cd $DIR && git pull && cd $T
fi
python manage.py load_40k_fixtures