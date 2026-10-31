// JapyScript — .NET interop runtime.
//
// Provides a managed host for JapyScript bytecode modules when a .NET
// application needs to execute JapyScript pipelines in-process. This is the
// managed binding; it does not embed any other language runtime.

using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;

namespace JapyScript.Bindings
{
    /// <summary>Status codes returned by the native JapyScript VM.</summary>
    public enum JpyStatus
    {
        Ok          = 0,
        CompileError = 1,
        RuntimeError = 2,
        NotFound     = 3,
    }

    /// <summary>A single execution context bound to one .jpc module.</summary>
    public sealed class JpyContext : IDisposable
    {
        private IntPtr _handle;
        private bool _disposed;

        public JpyContext(string modulePath)
        {
            if (!File.Exists(modulePath))
                throw new FileNotFoundException("module not found", modulePath);

            _handle = JpyNative.Create(modulePath);
            if (_handle == IntPtr.Zero)
                throw new InvalidOperationException("failed to create VM context");
        }

        public JpyStatus Invoke(string entry, object[] args, out object result)
        {
            result = null;
            if (_disposed) throw new ObjectDisposedException(nameof(JpyContext));
            if (args == null) args = Array.Empty<object>();

            var status = JpyNative.Invoke(_handle, entry, args, out var raw);
            if (status == JpyStatus.Ok)
                result = raw;
            return status;
        }

        public void Dispose()
        {
            if (_disposed) return;
            if (_handle != IntPtr.Zero)
            {
                JpyNative.Destroy(_handle);
                _handle = IntPtr.Zero;
            }
            _disposed = true;
            GC.SuppressFinalize(this);
        }

        ~JpyContext() { Dispose(); }
    }

    internal static class JpyNative
    {
        private const string Lib = "japyscript_vm";

        [DllImport(Lib, CallingConvention = CallingConvention.Cdecl)]
        public static extern IntPtr Create(string modulePath);

        [DllImport(Lib, CallingConvention = CallingConvention.Cdecl)]
        public static extern JpyStatus Invoke(
            IntPtr handle, string entry, object[] args, out object result);

        [DllImport(Lib, CallingConvention = CallingConvention.Cdecl)]
        public static extern void Destroy(IntPtr handle);
    }
}
