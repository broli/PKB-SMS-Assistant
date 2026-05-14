from PySide6.QtCore import QObject, QThread, Signal
import traceback

class BaseWorker(QObject):
    """
    Standardized base worker for executing long-running tasks in a separate thread.
    Handles boilerplate for error catching and standard signals.
    """
    finished = Signal()        # Emitted when _do_work completes successfully without returning data
    error = Signal(str)        # Emitted when an exception occurs
    status = Signal(str)       # Emitted for progress updates

    def __init__(self):
        super().__init__()

    def process(self):
        """
        The entry point for the thread. Wraps _do_work in a try-except block.
        Do not override this method. Override _do_work instead.
        """
        try:
            self._do_work()
        except Exception as e:
            err_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
            self.error.emit(err_msg)

    def _do_work(self):
        """
        Implement the actual task here. Emit custom signals or the standard 'finished' signal.
        """
        pass

def run_in_thread(worker: BaseWorker, parent_widget=None):
    """
    Safely executes a BaseWorker in a QThread.
    
    Args:
        worker: An instance of BaseWorker (or subclass).
        parent_widget: An optional UI widget to hold a reference to the thread
                       to prevent it from being garbage collected prematurely.
    """
    thread = QThread()
    worker.moveToThread(thread)

    # Lifecycle management
    thread.started.connect(worker.process)
    
    # We must ensure both the worker and thread are cleaned up when the thread finishes executing
    worker.finished.connect(thread.quit)
    worker.error.connect(thread.quit)
    
    # Optional signals for any custom finished signals your workers might have
    # If your worker has a custom signal like `data_fetched = Signal(dict)`, 
    # you'll need to connect it to thread.quit manually or ensure `finished` is also emitted.
    # We'll handle custom quit connections in the specific worker implementations.

    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    
    if parent_widget is not None:
        if not hasattr(parent_widget, '_active_threads'):
            parent_widget._active_threads = set()
        # Store both thread and worker to prevent Python GC from destroying the worker
        parent_widget._active_threads.add((thread, worker))
        
        def cleanup(t=thread, w=worker):
            if hasattr(parent_widget, '_active_threads'):
                parent_widget._active_threads.discard((t, w))
                
        thread.finished.connect(cleanup)

    thread.start()
    return thread
