; YTDownloader Windows 安装脚本 (Inno Setup)
[Setup]
AppName=YTDownloader
AppVersion=1.1.0
AppPublisher=3995 Hz
DefaultDirName={autopf}\YTDownloader
DefaultGroupName=YTDownloader
UninstallDisplayName=YTDownloader 视频下载器
OutputBaseFilename=YTDownloader-Setup
OutputDir=Output
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=assets\YTDownloader.ico
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "chinesesimplified"; MessagesFile: "Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\YTDownloader\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\YTDownloader"; Filename: "{app}\YTDownloader.exe"
Name: "{group}\{cm:UninstallProgram,YTDownloader}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\YTDownloader"; Filename: "{app}\YTDownloader.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\YTDownloader.exe"; Description: "{cm:LaunchProgram,YTDownloader}"; Flags: nowait postinstall skipifsilent
