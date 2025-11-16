# clone repo (if not already)
git clone https://github.com/classpippies-arch/class_game.git
cd class_game

# create branch (optional but recommended)
git checkout -b add-flappy-upload

# create file and paste content, or replace existing
# e.g. using a text editor:
# nano flappy_streamlit26.py
# (paste code -> save)

git add flappy_streamlit26.py
git commit -m "Add flappy_streamlit26.py (upload-enabled Flappy Streamlit game)"
git push -u origin add-flappy-upload

# then open GitHub and make a PR to main OR push directly to main if you want:
# (to push directly)
git checkout main
git merge add-flappy-upload
git push origin main
