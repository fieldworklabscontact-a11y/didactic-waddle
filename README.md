# didactic-waddle
Overview
Polyglot files combine two different formats into a single file—in this case, a WebM video at the front with a ZIP archive attached to the back.

The main catch is that tacking a ZIP onto a video shifts its internal data pointers. Standard extraction tools usually get confused by this and throw errors. This toolkit fixes that problem cleanly: the encrypter adjusts the pointers when building the file, and the extractor figures them out automatically when it's time to pull everything back out.

How It Works
1. The Encrypter (encrypt.py)
What it does: Takes any file or folder, compresses it into a ZIP, checks how long the WebM video is, and updates all the internal ZIP pointers so they account for the video size.

The Result: Outputs a single WebM file that plays like a normal video but holds your hidden data safely inside.

2. The Smart Extractor (extract.py)
What it does: Looks at the polyglot file to see how the pointers were set up.

The Result: If it finds absolute offsets (pointers that include the video size), it cleans them up safely in memory, skips any potential seek errors, and extracts your files smoothly.
