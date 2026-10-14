# me.arikatla.dev — talking-video portfolio

A second portfolio for **Sudheer Arikatla**: a 3D talking intro video in the hero, then About (swinging ID card), Skills (periodic table), Work, Certifications, Experience, Impact and Contact.

- Plain HTML, CSS and vanilla JS in `index.html` (no build step, no runtime CDNs). Fonts are self-hosted `.woff2` files.
- Hosted on GitHub Pages with the custom domain in `CNAME`.
- All text comes from the résumé (`Sudheer_Arikatla_Resume.pdf`) and the public GitHub repos.

## Rebuild the hero video
```
python3 build-hero-assets.py intro.mp4 .
```
Needs `ffmpeg` and `numpy`. It crops the character, whitens the background, makes a seamless 0.5 s video + audio cross-fade loop, and writes `hero.mp4`, `hero.webm` and `hero-poster.jpg`.

## Credits
- Character image and video generated with Google Gemini from Sudheer's own photos.
- Tech logos: [Devicon](https://devicon.dev) (MIT, see `LICENSE-devicon.txt`) and [Simple Icons](https://simpleicons.org) (CC0, see `LICENSE-simple-icons.txt`). Logos are trademarks of their owners.
- Fonts: Inter Tight, Instrument Serif, JetBrains Mono (SIL Open Font License).
