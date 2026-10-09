using System;
using System.IO;
using System.IO.Compression;
using System.Diagnostics;
using System.Windows.Forms;

class SfxStub
{
    [STAThread]
    static void Main()
    {
        try
        {
            string exePath = System.Reflection.Assembly.GetExecutingAssembly().Location;
            byte[] exeBytes = File.ReadAllBytes(exePath);

            string marker = "WHALEPET_ZIP_DATA_START";
            byte[] markerBytes = System.Text.Encoding.ASCII.GetBytes(marker);

            int markerPos = -1;
            for (int i = 0; i <= exeBytes.Length - markerBytes.Length; i++)
            {
                bool found = true;
                for (int j = 0; j < markerBytes.Length; j++)
                {
                    if (exeBytes[i + j] != markerBytes[j])
                    {
                        found = false;
                        break;
                    }
                }
                if (found)
                {
                    markerPos = i;
                    break;
                }
            }

            if (markerPos < 0)
            {
                MessageBox.Show("Installer data corrupted.", "Install Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            int zipStart = markerPos + markerBytes.Length;
            int zipLen = exeBytes.Length - zipStart;

            string tempDir = Path.Combine(Path.GetTempPath(), "whale_pet_install_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(tempDir);

            string zipPath = Path.Combine(tempDir, "_bundle.zip");
            using (FileStream fs = new FileStream(zipPath, FileMode.Create, FileAccess.Write))
            {
                fs.Write(exeBytes, zipStart, zipLen);
            }

            ZipFile.ExtractToDirectory(zipPath, tempDir);
            File.Delete(zipPath);

            string pythonw = Path.Combine(tempDir, "python", "pythonw.exe");
            string installerPy = Path.Combine(tempDir, "installer.py");
            if (!File.Exists(pythonw))
            {
                MessageBox.Show("Python runtime not found.", "Install Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = pythonw;
            psi.Arguments = "\"" + installerPy + "\"";
            psi.WorkingDirectory = tempDir;
            psi.UseShellExecute = false;
            psi.CreateNoWindow = true;
            Process.Start(psi);
        }
        catch (Exception ex)
        {
            MessageBox.Show("Installer launch failed:\n" + ex.Message, "Install Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}