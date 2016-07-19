if __name__ == '__main__':
    import main
    from PyQt4.QtGui import QApplication
    from os.path import join as pjoin
    import queue
    import sys
    import messages
    import resources

    main.app_path     = sys.path[0]
    main.app          = QApplication(sys.argv)

    messages.init_message_system()
    main.settings     = {
                    'raw_length'        : 1                                 ,
                    'preview_length'    : 1                                 ,
                    'filter_dir'        : pjoin(main.app_path, 'filter_plugin')  ,
                    'video_dir'         : pjoin(main.app_path, 'video_plugin')   ,
                    'analysis_dir'      : pjoin(main.app_path, 'analysis_plugin'),
                    'ui_dir'            : pjoin(main.app_path, 'ui')             ,
                    'log_dir'           : pjoin(main.app_path, 'log')            ,
                    'thread_exittimeout': 500                               ,
                    }
    main.previewqueue = queue.ICQueue(main.settings['preview_length'])
    main.rawqueue     = queue.ICQueue(main.settings['raw_length'])
    import analysis
    import main_window
    import worker_processor, worker_reader

    try:
        main.ic           = analysis.ICAnalysis()
        main.reader       = worker_reader.ICWorker_VIMOReader()
        main.processor    = worker_processor.ICWorker_Processor()
        main.mainwindow   = main_window.ICMainWindow()
        main.mainwindow.frm_playback.init()
        main.mainwindow.showMaximized()
        main.app.exec_()

        main.ic.release()
    except:
        import traceback
        traceback.print_exc()
    finally:
        main.reader.exit_and_wait()
        main.processor.exit_and_wait()
        resources.qCleanupResources()
        sys.exit(0)
