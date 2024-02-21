DIR="work_in_progress/battlescribe/fixtures/kill-team"
if [ ! -d "$DIR" ]; then
  git clone https://github.com/BSData/wh40k-killteam.git $DIR
else
  T=$(pwd)
  cd $DIR && git pull && cd $T
fi
python manage.py load_kt_fixtures