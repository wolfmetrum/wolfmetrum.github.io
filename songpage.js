// Computed data for song pages (zh and en): title, description and share image built in JS, so text is escaped once.
import { songTitle, songDescription } from './seo.js';

export default {
  eleventyComputed: {
    title: (d) => songTitle(d.work, d.t[d.lang]),
    description: (d) => songDescription(d.work, d.t[d.lang]),
    image: (d) => `https://i.ytimg.com/vi/${d.work.versions[0].youtube_id}/${d.work.versions[0].thumb === 'hq' ? 'hqdefault' : 'maxresdefault'}.jpg`,
  },
};
