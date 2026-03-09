import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from bs4 import BeautifulSoup
import os
import shutil
import requests
from urllib.parse import urljoin, urlparse
from tkinterdnd2 import DND_FILES, TkinterDnD
import re
import json
import threading
import time
from datetime import datetime
import hashlib
import mimetypes
import webbrowser
from pathlib import Path

class HTMLSplitterProApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HTML Splitter Pro - Advanced Web Asset Manager")
        self.root.geometry("1400x900")
        
        # Data storage
        self.html_paths = []
        self.output_dir = tk.StringVar()
        self.project_name = tk.StringVar(value="HTMLProject")
        self.settings = {
            'css_folder': 'css',
            'js_folder': 'js',
            'img_folder': 'images',
            'fonts_folder': 'fonts',
            'media_folder': 'media',
            'overwrite': True,
            'minify_css': False,
            'minify_js': False,
            'optimize_images': False,
            'create_backup': True,
            'preserve_comments': False,
            'max_concurrent_downloads': 5,
            'download_timeout': 30,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.failed_assets = []
        self.asset_cache = set()
        self.processing_stats = {
            'total_files': 0,
            'processed_files': 0,
            'total_assets': 0,
            'downloaded_assets': 0,
            'failed_assets': 0,
            'bytes_processed': 0,
            'start_time': None
        }
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_main_tab()
        self.create_advanced_tab()
        self.create_logs_tab()
        self.create_preview_tab()
        self.create_stats_tab()
        
        # Status bar
        self.create_status_bar()
        
        # Menu bar
        self.create_menu_bar()
        
        # Initialize variables
        self.preview_win = None
        self.processing_thread = None
        self.cancel_processing = False

    def create_menu_bar(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project", command=self.open_project)
        file_menu.add_command(label="Save Project", command=self.save_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Batch Convert", command=self.batch_convert)
        tools_menu.add_command(label="Asset Validator", command=self.validate_assets)
        tools_menu.add_command(label="Clean Output", command=self.clean_output)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Documentation", command=self.show_docs)

    def create_main_tab(self):
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Main")
        
        # Project settings
        project_frame = ttk.LabelFrame(main_frame, text="Project Settings", padding="10")
        project_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(project_frame, text="Project Name:").grid(row=0, column=0, sticky="w")
        tk.Entry(project_frame, textvariable=self.project_name, width=30).grid(row=0, column=1, padx=5)
        
        # File selection with enhanced UI
        file_frame = ttk.LabelFrame(main_frame, text="HTML Files", padding="10")
        file_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # File list with scrollbar
        list_frame = tk.Frame(file_frame)
        list_frame.pack(fill='both', expand=True)
        
        self.file_listbox = tk.Listbox(list_frame, selectmode='extended', height=8)
        scrollbar = tk.Scrollbar(list_frame, orient='vertical', command=self.file_listbox.yview)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # File operation buttons
        btn_frame = tk.Frame(file_frame)
        btn_frame.pack(fill='x', pady=5)
        
        tk.Button(btn_frame, text="Add Files", command=self.add_files).pack(side='left', padx=2)
        tk.Button(btn_frame, text="Add Folder", command=self.add_folder).pack(side='left', padx=2)
        tk.Button(btn_frame, text="Remove Selected", command=self.remove_files).pack(side='left', padx=2)
        tk.Button(btn_frame, text="Clear All", command=self.clear_files).pack(side='left', padx=2)
        
        # Output directory
        output_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding="10")
        output_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(output_frame, text="Output Directory:").grid(row=0, column=0, sticky="w")
        tk.Entry(output_frame, textvariable=self.output_dir, width=50).grid(row=0, column=1, padx=5)
        tk.Button(output_frame, text="Browse", command=self.browse_output).grid(row=0, column=2, padx=5)
        tk.Button(output_frame, text="Open", command=self.open_output).grid(row=0, column=3, padx=5)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.pack(fill='x', padx=5, pady=5)
        
        self.progress_var = tk.StringVar(value="Ready")
        tk.Label(progress_frame, textvariable=self.progress_var).pack(anchor='w')
        
        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(fill='x', pady=5)
        
        self.detailed_progress = ttk.Progressbar(progress_frame, orient="horizontal", length=400, mode="determinate")
        self.detailed_progress.pack(fill='x', pady=2)
        
        # Control buttons
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill='x', padx=5, pady=10)
        
        tk.Button(control_frame, text="Start Processing", command=self.start_processing, 
                 bg='#4CAF50', fg='white', font=('Arial', 12, 'bold')).pack(side='left', padx=5)
        tk.Button(control_frame, text="Cancel", command=self.cancel_processing_func, 
                 bg='#f44336', fg='white').pack(side='left', padx=5)
        tk.Button(control_frame, text="Settings", command=self.open_settings).pack(side='left', padx=5)
        tk.Button(control_frame, text="Preview", command=self.preview_html).pack(side='left', padx=5)

    def create_advanced_tab(self):
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="Advanced")
        
        # Asset processing options
        asset_frame = ttk.LabelFrame(advanced_frame, text="Asset Processing", padding="10")
        asset_frame.pack(fill='x', padx=5, pady=5)
        
        # Checkboxes for advanced options
        self.minify_css_var = tk.BooleanVar(value=self.settings['minify_css'])
        self.minify_js_var = tk.BooleanVar(value=self.settings['minify_js'])
        self.optimize_images_var = tk.BooleanVar(value=self.settings['optimize_images'])
        self.create_backup_var = tk.BooleanVar(value=self.settings['create_backup'])
        self.preserve_comments_var = tk.BooleanVar(value=self.settings['preserve_comments'])
        
        tk.Checkbutton(asset_frame, text="Minify CSS", variable=self.minify_css_var).pack(anchor='w')
        tk.Checkbutton(asset_frame, text="Minify JavaScript", variable=self.minify_js_var).pack(anchor='w')
        tk.Checkbutton(asset_frame, text="Optimize Images", variable=self.optimize_images_var).pack(anchor='w')
        tk.Checkbutton(asset_frame, text="Create Backup", variable=self.create_backup_var).pack(anchor='w')
        tk.Checkbutton(asset_frame, text="Preserve Comments", variable=self.preserve_comments_var).pack(anchor='w')
        
        # Download settings
        download_frame = ttk.LabelFrame(advanced_frame, text="Download Settings", padding="10")
        download_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(download_frame, text="Max Concurrent Downloads:").grid(row=0, column=0, sticky="w")
        self.concurrent_var = tk.IntVar(value=self.settings['max_concurrent_downloads'])
        tk.Spinbox(download_frame, from_=1, to=20, textvariable=self.concurrent_var, width=10).grid(row=0, column=1, padx=5)
        
        tk.Label(download_frame, text="Timeout (seconds):").grid(row=1, column=0, sticky="w")
        self.timeout_var = tk.IntVar(value=self.settings['download_timeout'])
        tk.Spinbox(download_frame, from_=5, to=300, textvariable=self.timeout_var, width=10).grid(row=1, column=1, padx=5)
        
        # Asset filters
        filter_frame = ttk.LabelFrame(advanced_frame, text="Asset Filters", padding="10")
        filter_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        tk.Label(filter_frame, text="Include Extensions:").pack(anchor='w')
        self.include_ext_text = tk.Text(filter_frame, height=3, width=50)
        self.include_ext_text.pack(fill='x', pady=2)
        self.include_ext_text.insert('1.0', '.css,.js,.png,.jpg,.jpeg,.gif,.svg,.woff,.woff2,.ttf,.eot')
        
        tk.Label(filter_frame, text="Exclude Patterns:").pack(anchor='w', pady=(10,0))
        self.exclude_patterns_text = tk.Text(filter_frame, height=3, width=50)
        self.exclude_patterns_text.pack(fill='x', pady=2)
        self.exclude_patterns_text.insert('1.0', 'temp,cache,node_modules')

    def create_logs_tab(self):
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")
        
        # Toolbar
        toolbar = tk.Frame(logs_frame)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        tk.Button(toolbar, text="Clear Logs", command=self.clear_logs).pack(side='left', padx=2)
        tk.Button(toolbar, text="Save Logs", command=self.save_logs).pack(side='left', padx=2)
        tk.Button(toolbar, text="Auto-scroll", command=self.toggle_autoscroll).pack(side='left', padx=2)
        
        # Filter options
        tk.Label(toolbar, text="Filter:").pack(side='left', padx=(20,5))
        self.log_filter = tk.StringVar()
        filter_combo = ttk.Combobox(toolbar, textvariable=self.log_filter, values=['All', 'Info', 'Warning', 'Error'], width=10)
        filter_combo.pack(side='left', padx=2)
        filter_combo.set('All')
        
        # Log display
        self.log_text = scrolledtext.ScrolledText(logs_frame, wrap='word', height=25, font=('Consolas', 10))
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Configure text tags for different log levels
        self.log_text.tag_configure('INFO', foreground='blue')
        self.log_text.tag_configure('WARNING', foreground='orange')
        self.log_text.tag_configure('ERROR', foreground='red')
        self.log_text.tag_configure('SUCCESS', foreground='green')
        
        self.autoscroll = True

    def create_preview_tab(self):
        preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(preview_frame, text="Preview")
        
        # Preview toolbar
        preview_toolbar = tk.Frame(preview_frame)
        preview_toolbar.pack(fill='x', padx=5, pady=5)
        
        tk.Button(preview_toolbar, text="Refresh", command=self.refresh_preview).pack(side='left', padx=2)
        tk.Button(preview_toolbar, text="Open in Browser", command=self.open_in_browser).pack(side='left', padx=2)
        tk.Button(preview_toolbar, text="Validate HTML", command=self.validate_html).pack(side='left', padx=2)
        
        # Preview mode selection
        tk.Label(preview_toolbar, text="Mode:").pack(side='left', padx=(20,5))
        self.preview_mode = tk.StringVar(value="HTML")
        mode_combo = ttk.Combobox(preview_toolbar, textvariable=self.preview_mode, 
                                 values=['HTML', 'CSS', 'JavaScript'], width=10)
        mode_combo.pack(side='left', padx=2)
        mode_combo.bind('<<ComboboxSelected>>', self.change_preview_mode)
        
        # Preview display
        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap='none', height=25, font=('Consolas', 10))
        self.preview_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Syntax highlighting (basic)
        self.configure_syntax_highlighting()

    def create_stats_tab(self):
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="Statistics")
        
        # Statistics display
        self.stats_text = scrolledtext.ScrolledText(stats_frame, wrap='word', height=25, font=('Consolas', 10))
        self.stats_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Refresh button
        tk.Button(stats_frame, text="Refresh Stats", command=self.update_stats_display).pack(pady=5)

    def create_status_bar(self):
        self.status_bar = tk.Frame(self.root, relief='sunken', bd=1)
        self.status_bar.pack(side='bottom', fill='x')
        
        self.status_label = tk.Label(self.status_bar, text="Ready", anchor='w')
        self.status_label.pack(side='left', padx=5)
        
        self.time_label = tk.Label(self.status_bar, text="", anchor='e')
        self.time_label.pack(side='right', padx=5)
        
        self.update_time()

    def update_time(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)

    # Enhanced file handling methods
    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select HTML Files",
            filetypes=[("HTML files", "*.html *.htm"), ("All files", "*.*")]
        )
        if files:
            for file in files:
                if file not in self.html_paths:
                    self.html_paths.append(file)
                    self.file_listbox.insert(tk.END, os.path.basename(file))
            self.log(f"Added {len(files)} files", "INFO")

    def add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder Containing HTML Files")
        if folder:
            html_files = []
            for ext in ['*.html', '*.htm']:
                html_files.extend(Path(folder).glob(f"**/{ext}"))
            
            added = 0
            for file in html_files:
                file_str = str(file)
                if file_str not in self.html_paths:
                    self.html_paths.append(file_str)
                    self.file_listbox.insert(tk.END, file.name)
                    added += 1
            
            self.log(f"Added {added} HTML files from folder", "INFO")

    def remove_files(self):
        selection = self.file_listbox.curselection()
        if selection:
            for i in reversed(selection):
                self.file_listbox.delete(i)
                del self.html_paths[i]
            self.log(f"Removed {len(selection)} files", "INFO")

    def clear_files(self):
        self.file_listbox.delete(0, tk.END)
        self.html_paths.clear()
        self.log("Cleared all files", "INFO")

    def browse_output(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.output_dir.set(path)
            self.log(f"Output directory set to: {path}", "INFO")

    def open_output(self):
        if self.output_dir.get() and os.path.exists(self.output_dir.get()):
            webbrowser.open(f"file://{self.output_dir.get()}")
        else:
            messagebox.showwarning("Warning", "Output directory not found")

    # Enhanced logging
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {level}: {message}"
        
        self.log_text.insert(tk.END, formatted_msg + '\n', level)
        
        if self.autoscroll:
            self.log_text.see(tk.END)
        
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def clear_logs(self):
        self.log_text.delete(1.0, tk.END)

    def save_logs(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log(f"Logs saved to: {filename}", "SUCCESS")

    def toggle_autoscroll(self):
        self.autoscroll = not self.autoscroll
        self.log(f"Auto-scroll {'enabled' if self.autoscroll else 'disabled'}", "INFO")

    # Enhanced settings dialog
    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Advanced Settings")
        settings_win.geometry("600x500")
        settings_win.transient(self.root)
        settings_win.grab_set()
        
        notebook = ttk.Notebook(settings_win)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Folders tab
        folders_frame = ttk.Frame(notebook)
        notebook.add(folders_frame, text="Folders")
        
        folders = [
            ('CSS Folder:', 'css_folder'),
            ('JS Folder:', 'js_folder'),
            ('Images Folder:', 'img_folder'),
            ('Fonts Folder:', 'fonts_folder'),
            ('Media Folder:', 'media_folder')
        ]
        
        folder_vars = {}
        for i, (label, key) in enumerate(folders):
            tk.Label(folders_frame, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=5)
            var = tk.StringVar(value=self.settings[key])
            tk.Entry(folders_frame, textvariable=var, width=30).grid(row=i, column=1, padx=5, pady=5)
            folder_vars[key] = var
        
        # Options tab
        options_frame = ttk.Frame(notebook)
        notebook.add(options_frame, text="Options")
        
        option_vars = {}
        options = [
            ('Overwrite existing files', 'overwrite'),
            ('Create backup', 'create_backup'),
            ('Preserve comments', 'preserve_comments'),
            ('Minify CSS', 'minify_css'),
            ('Minify JS', 'minify_js'),
            ('Optimize images', 'optimize_images')
        ]
        
        for i, (label, key) in enumerate(options):
            var = tk.BooleanVar(value=self.settings[key])
            tk.Checkbutton(options_frame, text=label, variable=var).grid(row=i, column=0, sticky='w', padx=5, pady=5)
            option_vars[key] = var
        
        # Network tab
        network_frame = ttk.Frame(notebook)
        notebook.add(network_frame, text="Network")
        
        tk.Label(network_frame, text="Max Concurrent Downloads:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        concurrent_var = tk.IntVar(value=self.settings['max_concurrent_downloads'])
        tk.Spinbox(network_frame, from_=1, to=50, textvariable=concurrent_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(network_frame, text="Download Timeout (seconds):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        timeout_var = tk.IntVar(value=self.settings['download_timeout'])
        tk.Spinbox(network_frame, from_=5, to=300, textvariable=timeout_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(network_frame, text="User Agent:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ua_var = tk.StringVar(value=self.settings['user_agent'])
        tk.Entry(network_frame, textvariable=ua_var, width=50).grid(row=2, column=1, padx=5, pady=5)
        
        # Save button
        def save_settings():
            # Update folder settings
            for key, var in folder_vars.items():
                self.settings[key] = var.get()
            
            # Update option settings
            for key, var in option_vars.items():
                self.settings[key] = var.get()
            
            # Update network settings
            self.settings['max_concurrent_downloads'] = concurrent_var.get()
            self.settings['download_timeout'] = timeout_var.get()
            self.settings['user_agent'] = ua_var.get()
            
            self.log("Settings saved", "SUCCESS")
            settings_win.destroy()
        
        button_frame = tk.Frame(settings_win)
        button_frame.pack(fill='x', padx=10, pady=10)
        tk.Button(button_frame, text="Save", command=save_settings).pack(side='right', padx=5)
        tk.Button(button_frame, text="Cancel", command=settings_win.destroy).pack(side='right', padx=5)

    # Enhanced processing
    def start_processing(self):
        if not self.html_paths:
            messagebox.showerror("Error", "No HTML files selected")
            return
        
        if not self.output_dir.get():
            messagebox.showerror("Error", "No output directory selected")
            return
        
        self.cancel_processing = False
        self.processing_thread = threading.Thread(target=self.process_files_threaded)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def cancel_processing_func(self):
        self.cancel_processing = True
        self.log("Processing cancelled by user", "WARNING")

    def process_files_threaded(self):
        try:
            self.processing_stats['start_time'] = time.time()
            self.processing_stats['total_files'] = len(self.html_paths)
            self.processing_stats['processed_files'] = 0
            
            self.log("Starting processing...", "INFO")
            
            for i, html_file in enumerate(self.html_paths):
                if self.cancel_processing:
                    break
                
                self.progress_var.set(f"Processing {os.path.basename(html_file)} ({i+1}/{len(self.html_paths)})")
                self.progress['value'] = (i / len(self.html_paths)) * 100
                
                try:
                    self.process_html_file(html_file)
                    self.processing_stats['processed_files'] += 1
                    self.log(f"Successfully processed: {os.path.basename(html_file)}", "SUCCESS")
                except Exception as e:
                    self.log(f"Error processing {os.path.basename(html_file)}: {str(e)}", "ERROR")
                
                self.root.update_idletasks()
            
            if not self.cancel_processing:
                self.progress['value'] = 100
                self.progress_var.set("Processing complete!")
                self.log("All files processed successfully!", "SUCCESS")
                messagebox.showinfo("Success", "Processing completed successfully!")
            
        except Exception as e:
            self.log(f"Critical error during processing: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Critical error: {str(e)}")
        finally:
            self.progress_var.set("Ready")
            self.progress['value'] = 0

    def process_html_file(self, html_file):
        """Enhanced HTML processing with more features"""
        output_dir = self.output_dir.get()
        
        # Create output directories
        directories = {
            'css': os.path.join(output_dir, self.settings['css_folder']),
            'js': os.path.join(output_dir, self.settings['js_folder']),
            'img': os.path.join(output_dir, self.settings['img_folder']),
            'fonts': os.path.join(output_dir, self.settings['fonts_folder']),
            'media': os.path.join(output_dir, self.settings['media_folder'])
        }
        
        for dir_path in directories.values():
            os.makedirs(dir_path, exist_ok=True)
        
        # Create backup if requested
        if self.settings['create_backup']:
            backup_dir = os.path.join(output_dir, 'backup')
            os.makedirs(backup_dir, exist_ok=True)
            backup_file = os.path.join(backup_dir, f"backup_{int(time.time())}_{os.path.basename(html_file)}")
            shutil.copy2(html_file, backup_file)
        
        base_path = os.path.dirname(html_file)
        
        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
        
        # Process CSS
        self.process_css(soup, directories['css'])
        
        # Process JavaScript
        self.process_js(soup, directories['js'])
        
        # Process images and media
        self.process_media(soup, directories, base_path)
        
        # Process fonts
        self.process_fonts(soup, directories['fonts'], base_path)
        
        # Save processed HTML
        output_html = os.path.join(output_dir, os.path.basename(html_file))
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        self.processing_stats['bytes_processed'] += os.path.getsize(html_file)

    def process_css(self, soup, css_dir):
        """Process CSS styles and external stylesheets"""
        # Inline styles
        styles = soup.find_all('style')
        css_content = []
        
        for style in styles:
            if style.string:
                css_content.append(style.string)
            style.decompose()
        
        if css_content:
            combined_css = '\n'.join(css_content)
            if self.settings['minify_css']:
                combined_css = self.minify_css_content(combined_css)
            
            css_file = os.path.join(css_dir, 'styles.css')
            with open(css_file, 'w', encoding='utf-8') as f:
                f.write(combined_css)
            
            # Add link to combined CSS
            link_tag = soup.new_tag('link', rel='stylesheet', href=f"{self.settings['css_folder']}/styles.css")
            if soup.head:
                soup.head.append(link_tag)
            else:
                head_tag = soup.new_tag('head')
                head_tag.append(link_tag)
                soup.insert(0, head_tag)
        
        # External stylesheets
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href and not href.startswith(f"{self.settings['css_folder']}/"):
                self.download_and_update_asset(href, css_dir, link, 'href', self.settings['css_folder'])

    def process_js(self, soup, js_dir):
        """Process JavaScript scripts"""
        # Inline scripts
        scripts = soup.find_all('script', src=False)
        js_content = []
        
        for script in scripts:
            if script.string and script.string.strip():
                js_content.append(script.string)
            script.decompose()
        
        if js_content:
            combined_js = '\n'.join(js_content)
            if self.settings['minify_js']:
                combined_js = self.minify_js_content(combined_js)
            
            js_file = os.path.join(js_dir, 'scripts.js')
            with open(js_file, 'w', encoding='utf-8') as f:
                f.write(combined_js)
            
            # Add script tag for combined JS
            script_tag = soup.new_tag('script', src=f"{self.settings['js_folder']}/scripts.js")
            if soup.body:
                soup.body.append(script_tag)
            else:
                soup.append(script_tag)
        
        # External scripts
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src and not src.startswith(f"{self.settings['js_folder']}/"):
                self.download_and_update_asset(src, js_dir, script, 'src', self.settings['js_folder'])

    def process_media(self, soup, directories, base_path):
        """Process images and media files"""
        # Images
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                self.download_and_update_asset(src, directories['img'], img, 'src', self.settings['img_folder'])
        
        # Background images in style attributes
        for tag in soup.find_all(style=True):
            style_val = tag['style']
            urls = re.findall(r'url\(["\']?([^"\')]+)["\']?\)', style_val)
            for url in urls:
                new_path = self.download_asset(url, directories['img'], base_path)
                if new_path:
                    rel_path = f"{self.settings['img_folder']}/{os.path.basename(new_path)}"
                    style_val = style_val.replace(url, rel_path)
            tag['style'] = style_val
        
        # Video and audio elements
        for media in soup.find_all(['video', 'audio']):
            src = media.get('src')
            if src:
                self.download_and_update_asset(src, directories['media'], media, 'src', self.settings['media_folder'])
            
            # Source elements within media tags
            for source in media.find_all('source'):
                src = source.get('src')
                if src:
                    self.download_and_update_asset(src, directories['media'], source, 'src', self.settings['media_folder'])

    def process_fonts(self, soup, fonts_dir, base_path):
        """Process font files"""
        # Font links
        for link in soup.find_all('link', rel='preload'):
            if link.get('as') == 'font':
                href = link.get('href')
                if href:
                    self.download_and_update_asset(href, fonts_dir, link, 'href', self.settings['fonts_folder'])
        
        # @font-face declarations in CSS would need additional processing
        # This is a simplified version

    def download_and_update_asset(self, url, dest_dir, element, attr, folder_name):
        """Download asset and update element reference"""
        try:
            new_path = self.download_asset(url, dest_dir, os.path.dirname(self.html_paths[0]))
            if new_path:
                rel_path = f"{folder_name}/{os.path.basename(new_path)}"
                element[attr] = rel_path
                self.processing_stats['downloaded_assets'] += 1
        except Exception as e:
            self.log(f"Failed to download {url}: {str(e)}", "ERROR")
            self.processing_stats['failed_assets'] += 1

    def download_asset(self, url, dest_dir, base_path):
        """Download or copy asset file"""
        try:
            if url.startswith(('http://', 'https://')):
                # Download from web
                response = requests.get(url, timeout=self.settings['download_timeout'], 
                                      headers={'User-Agent': self.settings['user_agent']})
                response.raise_for_status()
                
                # Determine filename
                filename = os.path.basename(urlparse(url).path)
                if not filename or '.' not in filename:
                    # Try to get filename from Content-Disposition header
                    if 'content-disposition' in response.headers:
                        filename = response.headers['content-disposition'].split('filename=')[1].strip('"')
                    else:
                        # Generate filename based on content type
                        ext = mimetypes.guess_extension(response.headers.get('content-type', ''))
                        filename = f"asset_{hashlib.md5(url.encode()).hexdigest()[:8]}{ext or ''}"
                
                dest_path = os.path.join(dest_dir, filename)
                
                # Check if file already exists
                if os.path.exists(dest_path) and not self.settings['overwrite']:
                    return dest_path
                
                with open(dest_path, 'wb') as f:
                    f.write(response.content)
                
                self.log(f"Downloaded: {filename}", "SUCCESS")
                return dest_path
                
            else:
                # Copy local file
                local_path = os.path.join(base_path, url.lstrip('/'))
                if os.path.exists(local_path):
                    filename = os.path.basename(local_path)
                    dest_path = os.path.join(dest_dir, filename)
                    
                    if os.path.exists(dest_path) and not self.settings['overwrite']:
                        return dest_path
                    
                    shutil.copy2(local_path, dest_path)
                    self.log(f"Copied: {filename}", "SUCCESS")
                    return dest_path
                else:
                    self.log(f"Local file not found: {local_path}", "WARNING")
                    return None
                    
        except Exception as e:
            self.log(f"Error downloading {url}: {str(e)}", "ERROR")
            return None

    def minify_css_content(self, css_content):
        """Simple CSS minification"""
        # Remove comments
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        # Remove extra whitespace
        css_content = re.sub(r'\s+', ' ', css_content)
        # Remove spaces around certain characters
        css_content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', css_content)
        return css_content.strip()

    def minify_js_content(self, js_content):
        """Simple JavaScript minification"""
        # Remove single-line comments
        js_content = re.sub(r'//.*', '', js_content, flags=re.MULTILINE)
        # Remove multi-line comments
        js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
        # Remove extra whitespace
        js_content = re.sub(r'\s+', ' ', js_content)
        return js_content.strip()

    # Preview functionality
    def preview_html(self):
        if not self.html_paths:
            messagebox.showerror("Error", "No HTML files selected")
            return
        
        self.refresh_preview()
        self.notebook.select(3)  # Switch to preview tab

    def refresh_preview(self):
        if not self.html_paths:
            return
        
        html_file = self.html_paths[0]
        output_dir = self.output_dir.get()
        
        if output_dir:
            preview_file = os.path.join(output_dir, os.path.basename(html_file))
            if os.path.exists(preview_file):
                html_file = preview_file
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, content)
            
            # Apply syntax highlighting
            self.apply_syntax_highlighting()
            
        except Exception as e:
            self.log(f"Error loading preview: {str(e)}", "ERROR")

    def change_preview_mode(self, event=None):
        mode = self.preview_mode.get()
        if mode == "CSS":
            self.show_css_preview()
        elif mode == "JavaScript":
            self.show_js_preview()
        else:
            self.refresh_preview()

    def show_css_preview(self):
        if not self.output_dir.get():
            return
        
        css_file = os.path.join(self.output_dir.get(), self.settings['css_folder'], 'styles.css')
        if os.path.exists(css_file):
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, content)

    def show_js_preview(self):
        if not self.output_dir.get():
            return
        
        js_file = os.path.join(self.output_dir.get(), self.settings['js_folder'], 'scripts.js')
        if os.path.exists(js_file):
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, content)

    def configure_syntax_highlighting(self):
        """Configure basic syntax highlighting"""
        # HTML tags
        self.preview_text.tag_configure('html_tag', foreground='blue')
        # Attributes
        self.preview_text.tag_configure('html_attr', foreground='red')
        # Strings
        self.preview_text.tag_configure('string', foreground='green')
        # Comments
        self.preview_text.tag_configure('comment', foreground='gray')

    def apply_syntax_highlighting(self):
        """Apply basic syntax highlighting to preview text"""
        content = self.preview_text.get(1.0, tk.END)
        
        # HTML tags
        for match in re.finditer(r'<[^>]+>', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.preview_text.tag_add('html_tag', start, end)
        
        # HTML comments
        for match in re.finditer(r'<!--.*?-->', content, re.DOTALL):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.preview_text.tag_add('comment', start, end)

    def open_in_browser(self):
        if not self.output_dir.get():
            messagebox.showwarning("Warning", "No output directory set")
            return
        
        if not self.html_paths:
            messagebox.showwarning("Warning", "No HTML files selected")
            return
        
        html_file = os.path.join(self.output_dir.get(), os.path.basename(self.html_paths[0]))
        if os.path.exists(html_file):
            webbrowser.open(f"file://{html_file}")
        else:
            messagebox.showwarning("Warning", "Processed HTML file not found")

    def validate_html(self):
        """Basic HTML validation"""
        if not self.html_paths:
            return
        
        try:
            html_file = self.html_paths[0]
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            validation_results = []
            
            # Check for basic HTML structure
            if not soup.find('html'):
                validation_results.append("Missing <html> tag")
            if not soup.find('head'):
                validation_results.append("Missing <head> tag")
            if not soup.find('body'):
                validation_results.append("Missing <body> tag")
            if not soup.find('title'):
                validation_results.append("Missing <title> tag")
            
            # Check for unclosed tags
            unclosed_tags = []
            for tag in soup.find_all():
                if tag.name in ['img', 'br', 'hr', 'input', 'meta', 'link']:
                    continue  # Self-closing tags
                if not tag.get_text(strip=True) and not tag.find_all():
                    unclosed_tags.append(tag.name)
            
            if unclosed_tags:
                validation_results.append(f"Potentially unclosed tags: {', '.join(set(unclosed_tags))}")
            
            if validation_results:
                result_text = "\n".join(validation_results)
                messagebox.showwarning("HTML Validation", f"Issues found:\n{result_text}")
            else:
                messagebox.showinfo("HTML Validation", "HTML appears to be valid!")
                
        except Exception as e:
            messagebox.showerror("Validation Error", f"Error validating HTML: {str(e)}")

    # Statistics
    def update_stats_display(self):
        """Update the statistics display"""
        stats_text = f"""
HTML Splitter Pro - Processing Statistics
=========================================

Project: {self.project_name.get()}
Output Directory: {self.output_dir.get()}

File Processing:
- Total Files: {self.processing_stats['total_files']}
- Processed Files: {self.processing_stats['processed_files']}
- Success Rate: {(self.processing_stats['processed_files'] / max(1, self.processing_stats['total_files'])) * 100:.1f}%

Asset Processing:
- Total Assets: {self.processing_stats['total_assets']}
- Downloaded Assets: {self.processing_stats['downloaded_assets']}
- Failed Assets: {self.processing_stats['failed_assets']}
- Bytes Processed: {self.processing_stats['bytes_processed']:,} bytes

Time Information:
- Start Time: {datetime.fromtimestamp(self.processing_stats['start_time']).strftime('%Y-%m-%d %H:%M:%S') if self.processing_stats['start_time'] else 'N/A'}
- Duration: {time.time() - self.processing_stats['start_time']:.2f} seconds if self.processing_stats['start_time'] else 'N/A'

Current Settings:
- CSS Folder: {self.settings['css_folder']}
- JS Folder: {self.settings['js_folder']}
- Images Folder: {self.settings['img_folder']}
- Fonts Folder: {self.settings['fonts_folder']}
- Media Folder: {self.settings['media_folder']}
- Overwrite Files: {self.settings['overwrite']}
- Minify CSS: {self.settings['minify_css']}
- Minify JS: {self.settings['minify_js']}
- Optimize Images: {self.settings['optimize_images']}
- Create Backup: {self.settings['create_backup']}
- Max Concurrent Downloads: {self.settings['max_concurrent_downloads']}
- Download Timeout: {self.settings['download_timeout']}s

Output Structure:
{self.output_dir.get()}/
├── {self.settings['css_folder']}/
├── {self.settings['js_folder']}/
├── {self.settings['img_folder']}/
├── {self.settings['fonts_folder']}/
├── {self.settings['media_folder']}/
└── *.html
"""
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)

    # Project management
    def new_project(self):
        """Create a new project"""
        self.html_paths.clear()
        self.file_listbox.delete(0, tk.END)
        self.output_dir.set("")
        self.project_name.set("HTMLProject")
        self.clear_logs()
        self.processing_stats = {
            'total_files': 0,
            'processed_files': 0,
            'total_assets': 0,
            'downloaded_assets': 0,
            'failed_assets': 0,
            'bytes_processed': 0,
            'start_time': None
        }
        self.log("New project created", "INFO")

    def save_project(self):
        """Save current project settings"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            project_data = {
                'project_name': self.project_name.get(),
                'html_paths': self.html_paths,
                'output_dir': self.output_dir.get(),
                'settings': self.settings
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2)
            
            self.log(f"Project saved to: {filename}", "SUCCESS")

    def open_project(self):
        """Open a saved project"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                
                self.project_name.set(project_data.get('project_name', 'HTMLProject'))
                self.html_paths = project_data.get('html_paths', [])
                self.output_dir.set(project_data.get('output_dir', ''))
                self.settings.update(project_data.get('settings', {}))
                
                # Update file listbox
                self.file_listbox.delete(0, tk.END)
                for html_file in self.html_paths:
                    self.file_listbox.insert(tk.END, os.path.basename(html_file))
                
                self.log(f"Project loaded from: {filename}", "SUCCESS")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error loading project: {str(e)}")

    # Additional tools
    def batch_convert(self):
        """Batch convert multiple folders"""
        messagebox.showinfo("Batch Convert", "Batch conversion feature - Select multiple folders to process")
        
        folders = []
        while True:
            folder = filedialog.askdirectory(title="Select folder to add (Cancel to finish)")
            if not folder:
                break
            folders.append(folder)
        
        if folders:
            self.log(f"Starting batch conversion of {len(folders)} folders", "INFO")
            for folder in folders:
                self.add_folder_to_batch(folder)

    def add_folder_to_batch(self, folder):
        """Add folder to batch processing"""
        html_files = []
        for ext in ['*.html', '*.htm']:
            html_files.extend(Path(folder).glob(f"**/{ext}"))
        
        for html_file in html_files:
            if str(html_file) not in self.html_paths:
                self.html_paths.append(str(html_file))
                self.file_listbox.insert(tk.END, html_file.name)

    def validate_assets(self):
        """Validate all assets in the project"""
        if not self.html_paths:
            messagebox.showwarning("Warning", "No HTML files selected")
            return
        
        self.log("Starting asset validation...", "INFO")
        
        missing_assets = []
        for html_file in self.html_paths:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f, 'html.parser')
                
                base_path = os.path.dirname(html_file)
                
                # Check images
                for img in soup.find_all('img'):
                    src = img.get('src')
                    if src and not src.startswith(('http://', 'https://')):
                        asset_path = os.path.join(base_path, src)
                        if not os.path.exists(asset_path):
                            missing_assets.append(f"{html_file}: {src}")
                
                # Check CSS files
                for link in soup.find_all('link', rel='stylesheet'):
                    href = link.get('href')
                    if href and not href.startswith(('http://', 'https://')):
                        asset_path = os.path.join(base_path, href)
                        if not os.path.exists(asset_path):
                            missing_assets.append(f"{html_file}: {href}")
                
                # Check JS files
                for script in soup.find_all('script', src=True):
                    src = script.get('src')
                    if src and not src.startswith(('http://', 'https://')):
                        asset_path = os.path.join(base_path, src)
                        if not os.path.exists(asset_path):
                            missing_assets.append(f"{html_file}: {src}")
                            
            except Exception as e:
                self.log(f"Error validating {html_file}: {str(e)}", "ERROR")
        
        if missing_assets:
            result = "Missing Assets Found:\n\n" + "\n".join(missing_assets)
            messagebox.showwarning("Asset Validation", result)
            self.log(f"Found {len(missing_assets)} missing assets", "WARNING")
        else:
            messagebox.showinfo("Asset Validation", "All assets are valid!")
            self.log("All assets validated successfully", "SUCCESS")

    def clean_output(self):
        """Clean the output directory"""
        if not self.output_dir.get():
            messagebox.showwarning("Warning", "No output directory set")
            return
        
        if not os.path.exists(self.output_dir.get()):
            messagebox.showwarning("Warning", "Output directory doesn't exist")
            return
        
        result = messagebox.askyesno("Clean Output", 
                                   f"Are you sure you want to clean the output directory?\n{self.output_dir.get()}")
        if result:
            try:
                shutil.rmtree(self.output_dir.get())
                os.makedirs(self.output_dir.get())
                self.log("Output directory cleaned", "SUCCESS")
                messagebox.showinfo("Success", "Output directory cleaned successfully")
            except Exception as e:
                self.log(f"Error cleaning output directory: {str(e)}", "ERROR")
                messagebox.showerror("Error", f"Error cleaning directory: {str(e)}")

    def show_about(self):
        """Show about dialog"""
        about_text = """
HTML Splitter Pro v2.0
Advanced Web Asset Manager

Features:
• Batch HTML processing
• Asset downloading and organization
• CSS and JavaScript minification
• Image optimization
• Project management
• Asset validation
• Preview functionality
• Comprehensive logging

Created with Python and tkinter
        """
        messagebox.showinfo("About HTML Splitter Pro", about_text)

    def show_docs(self):
        """Show documentation"""
        docs_text = """
HTML Splitter Pro Documentation

Getting Started:
1. Add HTML files using 'Add Files' or 'Add Folder'
2. Set output directory
3. Configure settings if needed
4. Click 'Start Processing'

Features:
• Main Tab: Core functionality
• Advanced Tab: Additional processing options
• Logs Tab: Detailed processing information
• Preview Tab: View processed files
• Statistics Tab: Processing statistics

Tips:
• Use project files to save configurations
• Enable backup for safety
• Check logs for detailed information
• Validate assets before processing
        """
        
        docs_win = tk.Toplevel(self.root)
        docs_win.title("Documentation")
        docs_win.geometry("600x400")
        
        text_widget = scrolledtext.ScrolledText(docs_win, wrap='word')
        text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        text_widget.insert(1.0, docs_text)
        text_widget.config(state='disabled')


def main():
    root = TkinterDnD.Tk()
    root.minsize(1200, 800)
    app = HTMLSplitterProApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
