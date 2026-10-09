using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Text;
using System.Web.Script.Serialization;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace WhalePetOnlineInstaller
{
    public class InstallerForm : Form
    {
        private static readonly string[] CDN_SOURCES = new string[]
        {
            "https://gh-proxy.com/https://github.com/csdKK/whale-desktop-pet/releases/download/v1.0.0/",
            "https://ghproxy.net/https://github.com/csdKK/whale-desktop-pet/releases/download/v1.0.0/",
            "https://ghps.cc/https://github.com/csdKK/whale-desktop-pet/releases/download/v1.0.0/",
            "https://gh.api.99988866.xyz/https://github.com/csdKK/whale-desktop-pet/releases/download/v1.0.0/",
            "https://github.moeyy.xyz/https://github.com/csdKK/whale-desktop-pet/releases/download/v1.0.0/",
            "https://github.com/csdKK/whale-desktop-pet/releases/download/v1.0.0/",
        };
        private static readonly string MANIFEST_URL = "https://gh-proxy.com/https://github.com/csdKK/whale-desktop-pet/releases/download/v1.0.0/resources_manifest.json";

        private Label lblStatus;
        private ProgressBar progressBar;
        private Button btnInstall;
        private Button btnBrowse;
        private TextBox txtPath;
        private Label lblTitle;
        private Label lblSize;

        private string installDir = "";
        private HttpClient httpClient;
        private bool isInstalling = false;

        [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
        static extern bool SHCreateShortcut(string pszShortcutFile, string pszTargetFile, string pszArguments, string pszDescription, string pszIconFile, int iIconIndex);

        public InstallerForm()
        {
            httpClient = new HttpClient();
            httpClient.Timeout = TimeSpan.FromMinutes(10);
            try
            {
                ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072 | (SecurityProtocolType)768 | (SecurityProtocolType)192;
            }
            catch { }

            this.Text = "鲸鱼娘桌宠 - 在线安装";
            this.Width = 520;
            this.Height = 360;
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.BackColor = System.Drawing.Color.FromArgb(245, 247, 252);

            lblTitle = new Label();
            lblTitle.Text = "🐳 鲸鱼娘桌宠 在线安装";
            lblTitle.Font = new System.Drawing.Font("微软雅黑", 16, System.Drawing.FontStyle.Bold);
            lblTitle.AutoSize = true;
            lblTitle.Location = new System.Drawing.Point(30, 25);
            lblTitle.ForeColor = System.Drawing.Color.FromArgb(30, 60, 120);
            this.Controls.Add(lblTitle);

            Label lblPath = new Label();
            lblPath.Text = "安装目录：";
            lblPath.Location = new System.Drawing.Point(30, 80);
            lblPath.AutoSize = true;
            lblPath.ForeColor = System.Drawing.Color.FromArgb(60, 60, 60);
            this.Controls.Add(lblPath);

            txtPath = new TextBox();
            txtPath.Location = new System.Drawing.Point(30, 105);
            txtPath.Width = 360;
            txtPath.Text = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "DSH-FatFish");
            this.Controls.Add(txtPath);

            btnBrowse = new Button();
            btnBrowse.Text = "浏览...";
            btnBrowse.Location = new System.Drawing.Point(400, 103);
            btnBrowse.Width = 80;
            btnBrowse.Click += BtnBrowse_Click;
            this.Controls.Add(btnBrowse);

            lblSize = new Label();
            lblSize.Text = "总下载大小：正在获取...";
            lblSize.Location = new System.Drawing.Point(30, 145);
            lblSize.AutoSize = true;
            lblSize.ForeColor = System.Drawing.Color.FromArgb(100, 100, 100);
            this.Controls.Add(lblSize);

            lblStatus = new Label();
            lblStatus.Text = "就绪";
            lblStatus.Location = new System.Drawing.Point(30, 180);
            lblStatus.AutoSize = true;
            lblStatus.ForeColor = System.Drawing.Color.FromArgb(60, 60, 60);
            this.Controls.Add(lblStatus);

            progressBar = new ProgressBar();
            progressBar.Location = new System.Drawing.Point(30, 205);
            progressBar.Width = 450;
            progressBar.Height = 25;
            this.Controls.Add(progressBar);

            btnInstall = new Button();
            btnInstall.Text = "开始安装";
            btnInstall.Location = new System.Drawing.Point(180, 255);
            btnInstall.Width = 160;
            btnInstall.Height = 40;
            btnInstall.Font = new System.Drawing.Font("微软雅黑", 12, System.Drawing.FontStyle.Bold);
            btnInstall.BackColor = System.Drawing.Color.FromArgb(52, 152, 219);
            btnInstall.ForeColor = System.Drawing.Color.White;
            btnInstall.FlatStyle = FlatStyle.Flat;
            btnInstall.Click += BtnInstall_Click;
            this.Controls.Add(btnInstall);

            LoadManifestAsync();
        }

        private void BtnBrowse_Click(object sender, EventArgs e)
        {
            using (FolderBrowserDialog dlg = new FolderBrowserDialog())
            {
                dlg.Description = "选择安装目录";
                if (dlg.ShowDialog() == DialogResult.OK)
                {
                    txtPath.Text = Path.Combine(dlg.SelectedPath, "DSH-FatFish");
                }
            }
        }

        private JavaScriptSerializer serializer = new JavaScriptSerializer();
        private Dictionary<string, object> currentManifest = null;

        private async Task<string> FetchManifestJsonAsync()
        {
            string[] manifestUrls = new string[]
            {
                "https://gh-proxy.com/https://github.com/csdKK/whale-desktop-pet/releases/download/v1.0.0/resources_manifest.json",
                "https://ghproxy.net/https://github.com/csdKK/whale-desktop-pet/releases/download/v1.0.0/resources_manifest.json",
                "https://ghps.cc/https://github.com/csdKK/whale-desktop-pet/releases/download/v1.0.0/resources_manifest.json",
                "https://gh.api.99988866.xyz/https://github.com/csdKK/whale-desktop-pet/releases/download/v1.0.0/resources_manifest.json",
                "https://github.moeyy.xyz/https://github.com/csdKK/whale-desktop-pet/releases/download/v1.0.0/resources_manifest.json",
                "https://github.com/csdKK/whale-desktop-pet/releases/download/v1.0.0/resources_manifest.json",
            };
            System.Text.StringBuilder errors = new System.Text.StringBuilder();
            foreach (string url in manifestUrls)
            {
                try
                {
                    using (var cts = new System.Threading.CancellationTokenSource(15000))
                    {
                        using (var resp = await httpClient.GetAsync(url, cts.Token))
                        {
                            resp.EnsureSuccessStatusCode();
                            string content = await resp.Content.ReadAsStringAsync();
                            if (string.IsNullOrEmpty(content) || content.TrimStart().StartsWith("{"))
                            {
                                if (!string.IsNullOrEmpty(content) && content.TrimStart().StartsWith("{"))
                                    return content;
                                errors.AppendLine(url + " 返回内容为空");
                                continue;
                            }
                            errors.AppendLine(url + " 返回内容非 JSON（前50字符: " + (content.Length > 50 ? content.Substring(0, 50) : content) + "）");
                        }
                    }
                }
                catch (Exception ex)
                {
                    errors.AppendLine(url + " 失败: " + ex.Message);
                    continue;
                }
            }
            throw new Exception("所有镜像源均不可用\n\n" + errors.ToString());
        }

        private async Task LoadManifestAsync()
        {
            try
            {
                string json = await FetchManifestJsonAsync();
                currentManifest = serializer.Deserialize<Dictionary<string, object>>(json);
                long total = Convert.ToInt64(currentManifest["total_size"]);
                lblSize.Text = string.Format("总下载大小：{0:F1} MB（共 {1} 个文件）", total / 1024.0 / 1024.0, CountParts(currentManifest));
            }
            catch (Exception ex)
            {
                lblSize.Text = "获取资源信息失败，请检查网络连接";
                MessageBox.Show(string.Format("获取资源清单失败：{0}\n\n请确认网络连接正常后重试。", ex.Message), "错误", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private int CountParts(Dictionary<string, object> m)
        {
            int n = 0;
            var packages = (Dictionary<string, object>)m["packages"];
            foreach (var p in packages.Values)
            {
                var pkg = (Dictionary<string, object>)p;
                var parts = (System.Collections.ArrayList)pkg["parts"];
                n += parts.Count;
            }
            return n;
        }

        private async void BtnInstall_Click(object sender, EventArgs e)
        {
            if (isInstalling) return;
            isInstalling = true;
            btnInstall.Enabled = false;
            btnBrowse.Enabled = false;
            txtPath.ReadOnly = true;

            installDir = txtPath.Text.Trim();
            if (string.IsNullOrEmpty(installDir))
            {
                MessageBox.Show("请选择安装目录");
                isInstalling = false;
                btnInstall.Enabled = true;
                return;
            }

            try
            {
                await InstallAsync();
                MessageBox.Show("安装完成！桌面已创建快捷方式。", "成功", MessageBoxButtons.OK, MessageBoxIcon.Information);
                this.Close();
            }
            catch (Exception ex)
            {
                MessageBox.Show(string.Format("安装失败：{0}", ex.Message), "错误", MessageBoxButtons.OK, MessageBoxIcon.Error);
                lblStatus.Text = "安装失败";
            }
            finally
            {
                isInstalling = false;
                btnInstall.Enabled = true;
            }
        }

        private async Task InstallAsync()
        {
            lblStatus.Text = "正在获取资源清单...";
            progressBar.Value = 0;

            string json = await FetchManifestJsonAsync();
            var manifest = serializer.Deserialize<Dictionary<string, object>>(json);

            int totalParts = CountParts(manifest);
            int doneParts = 0;
            long totalBytes = Convert.ToInt64(manifest["total_size"]);
            long doneBytes = 0;

            string tempDir = Path.Combine(Path.GetTempPath(), "WhalePetInstall_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(tempDir);

            try
            {
                var packages = (Dictionary<string, object>)manifest["packages"];
                foreach (var pkgEntry in packages)
                {
                    var pkg = (Dictionary<string, object>)pkgEntry.Value;
                    string targetDir = Path.Combine(installDir, pkg["target_dir"].ToString());
                    Directory.CreateDirectory(targetDir);

                    var parts = (System.Collections.ArrayList)pkg["parts"];
                    foreach (var partObj in parts)
                    {
                        var part = (Dictionary<string, object>)partObj;
                        string partName = part["name"].ToString();
                        long partSize = Convert.ToInt64(part["size"]);
                        string partMd5 = part["md5"].ToString();

                        lblStatus.Text = string.Format("下载中：{0}（{1}/{2}）", partName, doneParts + 1, totalParts);
                        string partPath = Path.Combine(tempDir, partName);

                        bool downloaded = false;
                        foreach (string baseUrl in CDN_SOURCES)
                        {
                            string url = baseUrl + partName;
                            try
                            {
                                await DownloadWithProgressAsync(url, partPath, partMd5,
                                    (downloaded_bytes) =>
                                    {
                                        long overall = doneBytes + downloaded_bytes;
                                        int pct = (int)((double)overall / totalBytes * 100);
                                        progressBar.Value = Math.Min(pct, 100);
                                    });
                                downloaded = true;
                                break;
                            }
                            catch (Exception)
                            {
                                if (File.Exists(partPath)) File.Delete(partPath);
                                continue;
                            }
                        }
                        if (!downloaded)
                        {
                            throw new Exception(string.Format("下载失败（所有镜像源均不可用）：{0}", partName));
                        }

                        doneBytes += partSize;
                        doneParts++;
                        int overallPct = (int)((double)doneBytes / totalBytes * 100);
                        progressBar.Value = Math.Min(overallPct, 100);

                        lblStatus.Text = string.Format("解压中：{0}", partName);
                        SafeExtractToDirectory(partPath, targetDir);
                        File.Delete(partPath);
                    }
                }

                lblStatus.Text = "正在安装核心文件...";
                ExtractEmbeddedCore(installDir);

                lblStatus.Text = "创建快捷方式...";
                progressBar.Value = 99;

                string pythonExe = Path.Combine(installDir, "python", "pythonw.exe");
                string mainPy = Path.Combine(installDir, "main.py");
                CreateDesktopShortcut(pythonExe, mainPy);

                lblStatus.Text = "注册卸载信息...";
                CreateUninstallScript(installDir);
                RegisterUninstallEntry(installDir);

                progressBar.Value = 100;
                lblStatus.Text = "安装完成！";
            }
            finally
            {
                try { Directory.Delete(tempDir, true); } catch { }
            }
        }

        private void ExtractEmbeddedCore(string installDir)
        {
            string exePath = System.Reflection.Assembly.GetExecutingAssembly().Location;
            byte[] exeBytes = File.ReadAllBytes(exePath);
            byte[] marker = Encoding.ASCII.GetBytes("WHALEPET_CORE_ZIP_START");

            int markerIdx = -1;
            for (int i = exeBytes.Length - marker.Length - 1; i >= 0; i--)
            {
                bool found = true;
                for (int j = 0; j < marker.Length; j++)
                {
                    if (exeBytes[i + j] != marker[j])
                    {
                        found = false;
                        break;
                    }
                }
                if (found)
                {
                    markerIdx = i;
                    break;
                }
            }

            if (markerIdx < 0)
            {
                throw new Exception("安装包损坏：找不到核心文件");
            }

            int zipStart = markerIdx + marker.Length;
            string tempZip = Path.Combine(Path.GetTempPath(), "whale_core_" + Guid.NewGuid().ToString("N") + ".zip");
            using (var fs = new FileStream(tempZip, FileMode.Create))
            {
                fs.Write(exeBytes, zipStart, exeBytes.Length - zipStart);
            }

            try
            {
                SafeExtractToDirectory(tempZip, installDir);
            }
            finally
            {
                try { File.Delete(tempZip); } catch { }
            }
        }

        private void SafeExtractToDirectory(string zipPath, string targetDir)
        {
            Directory.CreateDirectory(targetDir);
            using (var archive = ZipFile.OpenRead(zipPath))
            {
                foreach (var entry in archive.Entries)
                {
                    string destPath = Path.Combine(targetDir, entry.FullName);
                    string destParent = Path.GetDirectoryName(destPath);
                    if (!string.IsNullOrEmpty(destParent))
                    {
                        Directory.CreateDirectory(destParent);
                    }
                    if (entry.FullName.EndsWith("/") || entry.FullName.EndsWith("\\"))
                    {
                        Directory.CreateDirectory(destPath);
                    }
                    else
                    {
                        if (File.Exists(destPath))
                        {
                            File.Delete(destPath);
                        }
                        entry.ExtractToFile(destPath);
                    }
                }
            }
        }

        private async Task DownloadWithProgressAsync(string url, string destPath, string expectedMd5, Action<long> onProgress)
        {
            for (int attempt = 0; attempt < 3; attempt++)
            {
                try
                {
                    using (var cts = new System.Threading.CancellationTokenSource(30000))
                    using (var response = await httpClient.GetAsync(url, HttpCompletionOption.ResponseHeadersRead, cts.Token))
                    {
                        response.EnsureSuccessStatusCode();
                        long? totalBytes = response.Content.Headers.ContentLength;

                        using (var fs = new FileStream(destPath, FileMode.Create, FileAccess.Write, FileShare.None))
                        {
                            using (var stream = await response.Content.ReadAsStreamAsync())
                            {
                                byte[] buffer = new byte[81920];
                                long downloaded = 0;
                                int read;
                                while ((read = await stream.ReadAsync(buffer, 0, buffer.Length)) > 0)
                                {
                                    fs.Write(buffer, 0, read);
                                    downloaded += read;
                                    onProgress(downloaded);
                                }
                            }
                        }
                    }

                    if (!string.IsNullOrEmpty(expectedMd5))
                    {
                        string actual = ComputeMd5(destPath);
                        if (!actual.Equals(expectedMd5, StringComparison.OrdinalIgnoreCase))
                        {
                            File.Delete(destPath);
                            throw new Exception(string.Format("MD5 校验失败，重试中 ({0}/3)", attempt + 1));
                        }
                    }
                    return;
                }
                catch (Exception)
                {
                    if (attempt < 2)
                    {
                        if (File.Exists(destPath)) File.Delete(destPath);
                        System.Threading.Thread.Sleep(1000 * (attempt + 1));
                    }
                    else
                    {
                        throw new Exception("下载失败：网络异常");
                    }
                }
            }
        }

        private string ComputeMd5(string path)
        {
            using (var md5 = System.Security.Cryptography.MD5.Create())
            using (var stream = File.OpenRead(path))
            {
                byte[] hash = md5.ComputeHash(stream);
                StringBuilder sb = new StringBuilder();
                foreach (byte b in hash) sb.Append(b.ToString("x2"));
                return sb.ToString();
            }
        }

        private void CreateDesktopShortcut(string targetExe, string mainPy)
        {
            string desktop = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
            string shortcutPath = Path.Combine(desktop, "鲸鱼娘桌宠.lnk");

            dynamic shell = Activator.CreateInstance(Type.GetTypeFromProgID("WScript.Shell"));
            dynamic shortcut = shell.CreateShortcut(shortcutPath);
            shortcut.TargetPath = targetExe;
            shortcut.Arguments = "\"" + mainPy + "\"";
            shortcut.WorkingDirectory = installDir;
            shortcut.Description = "鲸鱼娘桌宠 DSH-FatFish";
            try
            {
                shortcut.IconLocation = Path.Combine(installDir, "圆角-蓝色大肥鱼.ico");
            }
            catch { }
            shortcut.Save();

            string startMenuDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.StartMenu), "Programs", "鲸鱼娘桌宠");
            Directory.CreateDirectory(startMenuDir);
            string startMenuLnk = Path.Combine(startMenuDir, "鲸鱼娘桌宠.lnk");
            dynamic smShortcut = shell.CreateShortcut(startMenuLnk);
            smShortcut.TargetPath = targetExe;
            smShortcut.Arguments = "\"" + mainPy + "\"";
            smShortcut.WorkingDirectory = installDir;
            smShortcut.Save();
        }

        private void CreateUninstallScript(string installDir)
        {
            string uninstallBat = Path.Combine(installDir, "uninstall.bat");
            string startMenuDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.StartMenu), "Programs", "鲸鱼娘桌宠");
            string desktopLnk = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "鲸鱼娘桌宠.lnk");
            string regExe = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "reg.exe");

            StringBuilder sb = new StringBuilder();
            sb.Append("@echo off\r\n");
            sb.Append("echo 正在卸载鲸鱼娘桌宠...\r\n");
            sb.Append("timeout /t 1 >nul\r\n");
            sb.Append("taskkill /f /im pythonw.exe 2>nul\r\n");
            sb.Append("taskkill /f /im python.exe 2>nul\r\n");
            sb.Append("echo 删除快捷方式...\r\n");
            sb.Append("del /q \"" + desktopLnk.Replace("\\", "\\\\") + "\" 2>nul\r\n");
            sb.Append("rmdir /s /q \"" + startMenuDir.Replace("\\", "\\\\") + "\" 2>nul\r\n");
            sb.Append("echo 删除注册表项...\r\n");
            sb.Append("\"" + regExe.Replace("\\", "\\\\") + "\" delete \"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\WhalePet\" /f >nul 2>nul\r\n");
            sb.Append("echo 删除安装目录...\r\n");
            sb.Append("cd /d \"" + installDir.Replace("\\", "\\\\") + "\"\r\n");
            sb.Append("cd ..\r\n");
            sb.Append("rmdir /s /q \"" + installDir.Replace("\\", "\\\\") + "\" 2>nul\r\n");
            sb.Append("echo 卸载完成！\r\n");
            sb.Append("timeout /t 2 >nul\r\n");

            File.WriteAllText(uninstallBat, sb.ToString(), Encoding.Default);
        }

        private void RegisterUninstallEntry(string installDir)
        {
            try
            {
                string uninstallBat = Path.Combine(installDir, "uninstall.bat");
                string regPath = @"Software\Microsoft\Windows\CurrentVersion\Uninstall\WhalePet";

                using (Microsoft.Win32.RegistryKey key = Microsoft.Win32.Registry.CurrentUser.CreateSubKey(regPath))
                {
                    if (key != null)
                    {
                        key.SetValue("DisplayName", "鲸鱼娘桌宠");
                        key.SetValue("DisplayVersion", "1.0.0");
                        key.SetValue("Publisher", "csdKK");
                        key.SetValue("InstallLocation", installDir);
                        key.SetValue("UninstallString", "\"" + uninstallBat + "\"");
                        key.SetValue("DisplayIcon", Path.Combine(installDir, "圆角-蓝色大肥鱼.ico"));
                        key.SetValue("EstimatedSize", 1578 * 1024, Microsoft.Win32.RegistryValueKind.DWord);
                        key.SetValue("NoModify", 1, Microsoft.Win32.RegistryValueKind.DWord);
                        key.SetValue("NoRepair", 1, Microsoft.Win32.RegistryValueKind.DWord);
                        key.Close();
                    }
                }
            }
            catch (Exception ex)
            {
                throw new Exception(string.Format("注册表写入失败：{0}", ex.Message));
            }
        }
    }

    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new InstallerForm());
        }
    }
}