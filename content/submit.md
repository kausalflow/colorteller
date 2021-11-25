---
title: "Submit New Color Palettes"
date: 2020-04-26T14:25:39+02:00
draft: false
---

{{< message >}}

**All submitted content will be licensed** under [the **CC BY-SA** license](https://creativecommons.org/licenses/by-sa/4.0/). Under this license, everyone, including you, can access and use the content on this website freely. **Please don't submit anything if you don't agree with this license.**

On how to use the open content, please refer to [the About page](/about/).

{{< /message >}}

There are two ways to submit a new color palette.

## Using Our Form

We have created a form for you to submit new color palettes. We will regularly collect the results and integrate them into our website.

{{< netlify-form >}}

We pull data from this form automatically and create a [Pull Request on GitHub](https://github.com/kausalflow/colorteller/pulls). Not every tool will be merged. The unmerged tools will be shown in the list of [PRs](https://github.com/kausalflow/colorteller/pulls).


## OR Create a Pull Request on GitHub

If your are familiar with GitHub, please create a new Pull Request here: [kausalflow/colorteller](https://github.com/kausalflow/colorteller/pulls)

We use [Hugo](https://gohugo.io/) to generate the website.

1. Install [Hugo](https://gohugo.io/)
2. Fork the repo [kausalflow/colorteller](https://github.com/kausalflow/colorteller)
3. `hugo new colors/name-of-palette.md`
4. Edit the new file in `content/colors/name-of-palette.md`
5. Commit, Push, and Create PR on GitHub

If you prefer **not** to install Hugo:

1. Fork the repo [kausalflow/colorteller](https://github.com/kausalflow/colorteller)
2. Create a new file `content/colors/name-of-color.md` with the following content
3. Fill in the fields in the new file. If it is unclear what to type in, please refer to existing color palettes inside `content/colors/`.
4. Commit, Push, and Create PR on GitHub.
