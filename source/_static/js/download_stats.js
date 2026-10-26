const downloadStatsURL = "https://storage.googleapis.com/invest-plugin-registry/plugin_download_stats.json";

async function fetchDownloadStats(pluginID) {
  try {
    const response = await fetch(downloadStatsURL);
    if (!response.ok) {
      throw new Error(`Error fetching download stats. Response status: ${response.status}`);
    }
    const downloadStatsJSON = await response.json();
    const downloadStats = downloadStatsJSON.data;
    if (downloadStats.hasOwnProperty(pluginID)){
      return downloadStats[pluginID];
    } else {
      return "0";
    }
  } catch (error) {
    console.log(error.message);
    return null;
  }
}

async function getDownloadCount() {
  // pyproject.toml.project.name === dist_package_name; it's the primary key
  // used by the Registry and is also used as the key in plugin_download_stats.json
  let pluginID = document.getElementsByClassName("dist-package-name")[0].innerText.trim();
  const downloadCount = await fetchDownloadStats(pluginID);

  let downloadEl = null;
  // The section at the top of the Plugin page containing the "Downloads"
  // element is a div with class="line-block"; each item within that div
  // is a div with class="line". Get all elements with ClassName "line"
  // and iterate to find the one with text "Downloads:"
  let lines = document.getElementsByClassName("line");
  for (const item of lines) {
    if (item.innerText === "Downloads:") {
      downloadEl = item;
      break;
    }
  }

  // only update download count if no error occured in JSON fetch
  if (downloadCount !== null) {
    downloadEl.innerHTML += ` ${downloadCount}`;
  }
}

document.addEventListener("DOMContentLoaded", function() {
  getDownloadCount();
});